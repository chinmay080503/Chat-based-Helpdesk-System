from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import timedelta
import json

from .models import User, Ticket, KnowledgeBase, Message


# ── Auth ──────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    error = None
    if request.method == 'POST':
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user:
            login(request, user)
            return redirect('dashboard')
        error = 'Invalid credentials'
    return render(request, 'core/login.html', {'error': error})


def logout_view(request):
    logout(request)
    return redirect('login')


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    user = request.user
    if user.role == 'admin':
        tickets = Ticket.objects.all()
    elif user.role == 'agent':
        tickets = Ticket.objects.filter(assigned_to=user)
    else:
        tickets = Ticket.objects.filter(created_by=user)

    stats = {
        'total': tickets.count(),
        'open': tickets.filter(status='open').count(),
        'in_progress': tickets.filter(status='in_progress').count(),
        'resolved': tickets.filter(status='resolved').count(),
    }
    recent = tickets.order_by('-created_at')[:5]
    return render(request, 'core/dashboard.html', {'stats': stats, 'recent': recent})


# ── Tickets ───────────────────────────────────────────────────────────────────

@login_required
def tickets_view(request):
    user = request.user
    if user.role == 'admin':
        tickets = Ticket.objects.all()
    elif user.role == 'agent':
        tickets = Ticket.objects.filter(assigned_to=user)
    else:
        tickets = Ticket.objects.filter(created_by=user)

    status_f = request.GET.get('status', '')
    priority_f = request.GET.get('priority', '')
    if status_f:
        tickets = tickets.filter(status=status_f)
    if priority_f:
        tickets = tickets.filter(priority=priority_f)

    agents = User.objects.filter(role='agent')
    return render(request, 'core/tickets.html', {'tickets': tickets.order_by('-created_at'), 'agents': agents})


@login_required
def create_ticket(request):
    if request.method == 'POST':
        Ticket.objects.create(
            title=request.POST['title'],
            description=request.POST['description'],
            priority=request.POST.get('priority', 'medium'),
            created_by=request.user,
        )
    return redirect('tickets')


@login_required
def update_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        ticket.status = request.POST.get('status', ticket.status)
        ticket.priority = request.POST.get('priority', ticket.priority)
        agent_id = request.POST.get('assigned_to')
        if agent_id:
            ticket.assigned_to = User.objects.filter(pk=agent_id).first()
        if ticket.status == 'resolved' and not ticket.resolved_at:
            ticket.resolved_at = timezone.now()
        ticket.save()
    return redirect('tickets')


@login_required
def delete_ticket(request, pk):
    if request.user.role == 'admin':
        get_object_or_404(Ticket, pk=pk).delete()
    return redirect('tickets')


# ── Chat / Bot ─────────────────────────────────────────────────────────────────

@login_required
def chat_view(request):
    messages = Message.objects.filter(sender=request.user, ticket__isnull=True).order_by('created_at')
    kb_suggestions = KnowledgeBase.objects.all()[:6]
    return render(request, 'core/chat.html', {'messages': messages, 'kb_suggestions': kb_suggestions})


@login_required
def chat_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    data = json.loads(request.body)
    user_msg = data.get('message', '').strip()
    if not user_msg:
        return JsonResponse({'error': 'Empty'}, status=400)

    Message.objects.create(sender=request.user, content=user_msg, is_bot=False)

    # Bot: search KB — ignore stop words, require whole-word matches, min threshold
    import re
    STOP_WORDS = {'a','an','the','is','it','in','on','at','to','do','my','me','we',
                  'he','she','they','you','of','or','and','for','are','was','be',
                  'by','so','if','as','up','but','not','can','has','had','how',
                  'why','what','when','where','who','which','this','that','with',
                  'from','have','will','its','about','please','help','i'}
    words = [w for w in re.findall(r'[a-z]+', user_msg.lower())
             if w not in STOP_WORDS and len(w) > 2]

    kb_entries = KnowledgeBase.objects.all()
    best, best_score = None, 0
    for entry in kb_entries:
        q_kw = (entry.question + ' ' + entry.keywords).lower()
        ans   = entry.answer.lower()
        # question/keyword match = 2pts each, answer match = 1pt each (whole words only)
        score  = sum(2 for w in words if re.search(r'\b' + re.escape(w) + r'\b', q_kw))
        score += sum(1 for w in words if re.search(r'\b' + re.escape(w) + r'\b', ans))
        if score > best_score:
            best, best_score = entry, score

    # Require at least 2 points to avoid false positives on unrelated messages
    if best and best_score >= 2:
        bot_text = f"📚 {best.answer}"
        ticket_created = False
    else:
        # Auto-create ticket
        ticket = Ticket.objects.create(
            title=f"Auto: {user_msg[:80]}",
            description=user_msg,
            created_by=request.user,
        )
        bot_text = f"I couldn't find an answer. A support ticket #{ticket.id} has been created for you. Our team will follow up shortly."
        ticket_created = True

    Message.objects.create(sender=request.user, content=bot_text, is_bot=True)
    return JsonResponse({'reply': bot_text, 'ticket_created': ticket_created})


# ── Knowledge Base ────────────────────────────────────────────────────────────

@login_required
def kb_view(request):
    q = request.GET.get('q', '')
    entries = KnowledgeBase.objects.filter(
        Q(question__icontains=q) | Q(answer__icontains=q) | Q(keywords__icontains=q)
    ) if q else KnowledgeBase.objects.all()
    return render(request, 'core/knowledge_base.html', {'entries': entries, 'q': q})


@login_required
def kb_create(request):
    if request.method == 'POST' and request.user.role in ('admin', 'agent'):
        KnowledgeBase.objects.create(
            question=request.POST['question'],
            answer=request.POST['answer'],
            keywords=request.POST.get('keywords', ''),
        )
    return redirect('knowledge_base')


@login_required
def kb_delete(request, pk):
    if request.user.role == 'admin':
        get_object_or_404(KnowledgeBase, pk=pk).delete()
    return redirect('knowledge_base')


# ── Analytics ─────────────────────────────────────────────────────────────────

@login_required
def analytics_view(request):
    if request.user.role not in ('admin', 'agent'):
        return redirect('dashboard')

    tickets = Ticket.objects.all()
    total = tickets.count()

    # Ticket trends last 7 days
    days, day_counts = [], []
    for i in range(6, -1, -1):
        d = timezone.now().date() - timedelta(days=i)
        days.append(d.strftime('%b %d'))
        day_counts.append(tickets.filter(created_at__date=d).count())

    # Resolution time (hours)
    resolved = tickets.filter(resolved_at__isnull=False)
    res_times = []
    for t in resolved:
        diff = (t.resolved_at - t.created_at).total_seconds() / 3600
        res_times.append(round(diff, 1))
    avg_res = round(sum(res_times) / len(res_times), 1) if res_times else 0

    # Status breakdown
    statuses = ['open', 'in_progress', 'resolved', 'closed']
    status_counts = [tickets.filter(status=s).count() for s in statuses]

    # Bot performance
    total_chats = Message.objects.filter(is_bot=True).count()
    auto_tickets = tickets.filter(title__startswith='Auto:').count()
    bot_resolved = max(0, total_chats - auto_tickets)

    # Agent performance
    agents = User.objects.filter(role='agent')
    agent_data = []
    for a in agents:
        at = tickets.filter(assigned_to=a)
        agent_data.append({
            'name': a.get_full_name() or a.username,
            'total': at.count(),
            'resolved': at.filter(status='resolved').count(),
        })

    context = {
        'total': total, 'avg_res': avg_res,
        'days': json.dumps(days), 'day_counts': json.dumps(day_counts),
        'statuses': json.dumps([s.replace('_', ' ').title() for s in statuses]),
        'status_counts': json.dumps(status_counts),
        'bot_resolved': bot_resolved, 'auto_tickets': auto_tickets, 'total_chats': total_chats,
        'agent_data': agent_data,
    }
    return render(request, 'core/analytics.html', context)


# ── Profile ───────────────────────────────────────────────────────────────────

@login_required
def profile_view(request):
    if request.method == 'POST':
        u = request.user
        u.first_name = request.POST.get('first_name', u.first_name)
        u.last_name = request.POST.get('last_name', u.last_name)
        u.email = request.POST.get('email', u.email)
        u.bio = request.POST.get('bio', u.bio)
        pw = request.POST.get('password')
        if pw:
            u.set_password(pw)
        u.save()
        if pw:
            login(request, u)
        return redirect('profile')
    return render(request, 'core/profile.html')