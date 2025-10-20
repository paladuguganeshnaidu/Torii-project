def test_sms_tool(request):
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').lower()
    spammy = any(k in text for k in ['win', 'free', 'prize', 'click', 'urgent'])
    return {
        'tool': 'sms-spam-tester',
        'length': len(text),
        'spam_score': (2 if spammy else 0),
        'label': 'spam' if spammy else 'ham',
        'note': 'Stub rule-based classifier.'
    }
