def recon_target_tool(request):
    data = request.get_json(silent=True) or {}
    target = (data.get('target') or '').strip()
    return {
        'tool': 'web-recon',
        'target': target,
        'whois': 'N/A (stub)',
        'dns': {'A': [], 'MX': []},
        'note': 'No network calls. Replace with real recon.'
    }
