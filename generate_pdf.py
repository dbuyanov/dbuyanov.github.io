#!/usr/bin/env python3
"""
Aucta AI — PDF Offer Generator
Usage: python3 generate_pdf.py --lang ru|en|ro
"""

import argparse
import json
import os
import re
import sys

def flow_svg(steps, color='#8b5cf6'):
    bw, bh, gap = 58, 24, 14
    W = len(steps) * bw + (len(steps) - 1) * gap + 8
    H = 38
    out = f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:{W}px;height:{H}px;display:block">'
    x = 4
    for i, s in enumerate(steps):
        # Box
        out += (f'<rect x="{x}" y="{(H-bh)//2}" width="{bw}" height="{bh}" rx="5" '
                f'fill="rgba(99,102,241,0.1)" stroke="{color}" stroke-opacity="0.35" stroke-width="1"/>')
        # Text (two lines if needed)
        if len(s) > 10:
            words = s.split()
            mid = len(words) // 2
            line1 = ' '.join(words[:mid])
            line2 = ' '.join(words[mid:])
            cy = H // 2
            out += (f'<text x="{x+bw//2}" y="{cy-3}" text-anchor="middle" '
                    f'font-size="6.5" fill="#c4b5fd" font-family="Inter,sans-serif" font-weight="600">{line1}</text>')
            out += (f'<text x="{x+bw//2}" y="{cy+8}" text-anchor="middle" '
                    f'font-size="6.5" fill="#c4b5fd" font-family="Inter,sans-serif" font-weight="600">{line2}</text>')
        else:
            out += (f'<text x="{x+bw//2}" y="{H//2+3}" text-anchor="middle" '
                    f'font-size="6.5" fill="#c4b5fd" font-family="Inter,sans-serif" font-weight="600">{s}</text>')
        # Arrow
        if i < len(steps) - 1:
            ax = x + bw
            out += (f'<line x1="{ax+1}" y1="{H//2}" x2="{ax+gap-4}" y2="{H//2}" '
                    f'stroke="{color}" stroke-opacity="0.55" stroke-width="1.3"/>'
                    f'<polygon points="{ax+gap-4},{H//2-3} {ax+gap},{H//2} {ax+gap-4},{H//2+3}" '
                    f'fill="{color}" opacity="0.7"/>')
        x += bw + gap
    return out + '</svg>'


SERVICE_ICONS_SVG = [
    # chatbot
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a5b4fc" stroke-width="1.8" stroke-linecap="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>',
    # leads/funnel
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a5b4fc" stroke-width="1.8" stroke-linecap="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>',
    # email
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a5b4fc" stroke-width="1.8" stroke-linecap="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>',
    # microphone/calls
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a5b4fc" stroke-width="1.8" stroke-linecap="round"><path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/><path d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8"/></svg>',
    # database/RAG
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a5b4fc" stroke-width="1.8" stroke-linecap="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4.03 3-9 3S3 13.66 3 12"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/></svg>',
    # CRM/refresh
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a5b4fc" stroke-width="1.8" stroke-linecap="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>',
    # content/pen
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a5b4fc" stroke-width="1.8" stroke-linecap="round"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 013 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>',
    # data/file
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#a5b4fc" stroke-width="1.8" stroke-linecap="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
]


def render_template(html: str, ctx: dict) -> str:
    """Very simple Jinja2-like template renderer."""
    from jinja2 import Environment, BaseLoader
    env = Environment(loader=BaseLoader())
    env.globals['flow_svg'] = flow_svg
    env.globals['svc_icons'] = SERVICE_ICONS_SVG
    tmpl = env.from_string(html)
    return tmpl.render(**ctx)


def build_context(lang: str, texts: dict) -> dict:
    t = texts[lang]
    ctx = dict(t)
    ctx['lang'] = lang

    # Cover eyebrow and tags by language
    eyebrows = {
        'ru': 'Коммерческое предложение',
        'en': 'Commercial Proposal',
        'ro': 'Ofertă comercială',
    }
    cover_tags_map = {
        'ru': ['ИИ-чатботы', 'Автоматизация лидов', 'CRM-интеграции', 'RAG-системы', 'Поддержка 24/7'],
        'en': ['AI Chatbots', 'Lead Automation', 'CRM Integrations', 'RAG Systems', '24/7 Support'],
        'ro': ['Chatboți AI', 'Automatizare lead-uri', 'Integrări CRM', 'Sisteme RAG', 'Suport 24/7'],
    }
    ctx['cover_eyebrow'] = eyebrows[lang]
    ctx['cover_tags'] = cover_tags_map[lang]

    # Stats labels on p2
    stats_map = {
        'ru': ('Часов в месяц освобождается', 'Ускорение обработки заявок', 'Макс. снижение затрат'),
        'en': ('Hours freed per month', 'Faster lead processing', 'Max cost reduction'),
        'ro': ('Ore eliberate pe lună', 'Procesare mai rapidă a lead-urilor', 'Reducere max. costuri'),
    }
    ctx['stat1'], ctx['stat2'], ctx['stat3'] = stats_map[lang]

    # Bridge on p3
    bridge_map = {
        'ru': {
            'bridge_title': 'Всё это — решаемые задачи.',
            'bridge_text': 'Ни одна из этих проблем не требует найма нового сотрудника или замены привычных систем. ИИ-автоматизация встраивается поверх того, что уже работает — и берёт рутину на себя.',
        },
        'en': {
            'bridge_title': 'All of these are solvable.',
            'bridge_text': 'None of these problems require hiring new staff or replacing your existing systems. AI automation layers on top of what you already have — and handles the routine for you.',
        },
        'ro': {
            'bridge_title': 'Toate acestea sunt probleme rezolvabile.',
            'bridge_text': 'Niciuna dintre aceste probleme nu necesită angajarea de personal nou sau înlocuirea sistemelor existente. Automatizarea AI se integrează peste ce ai deja — și preia rutina.',
        },
    }
    ctx.update(bridge_map[lang])

    p3_stats_map = {
        'ru': [
            {'num': '30–40%', 'label': 'рабочего\nвремени на рутину'},
            {'num': '2×', 'label': 'быстрее обработка\nзаявок'},
            {'num': '80%', 'label': 'снижение\nзатрат возможно'},
            {'num': '24/7', 'label': 'работа\nбез перерывов'},
        ],
        'en': [
            {'num': '30–40%', 'label': 'work time\non routine'},
            {'num': '2×', 'label': 'faster\nlead processing'},
            {'num': '80%', 'label': 'cost reduction\npossible'},
            {'num': '24/7', 'label': 'operation\nwithout breaks'},
        ],
        'ro': [
            {'num': '30–40%', 'label': 'timp de lucru\npe rutină'},
            {'num': '2×', 'label': 'procesare mai rapidă\na lead-urilor'},
            {'num': '80%', 'label': 'reducere\ncosturi posibilă'},
            {'num': '24/7', 'label': 'funcționare\nfără întreruperi'},
        ],
    }
    ctx['p3_stats'] = p3_stats_map[lang]

    # Integration note on p5
    integration_map = {
        'ru': {
            'integration_title': 'Всё интегрируется с тем, что у вас уже есть',
            'integration_text': 'Мы подключаемся к вашим существующим инструментам через API. Не нужно переносить данные или менять процессы — автоматизация встраивается поверх.',
        },
        'en': {
            'integration_title': 'Everything integrates with what you already have',
            'integration_text': 'We connect to your existing tools via API. No data migration or process changes needed — automation layers on top.',
        },
        'ro': {
            'integration_title': 'Totul se integrează cu ce ai deja',
            'integration_text': 'Ne conectăm la instrumentele tale existente prin API. Nu e nevoie de migrarea datelor sau schimbarea proceselor — automatizarea se integrează deasupra.',
        },
    }
    ctx.update(integration_map[lang])

    ctx['tools_list'] = ['n8n', 'Make', 'OpenAI API', 'Claude API', 'Telegram Bot API', 'WhatsApp Business API', 'Gmail API', 'HubSpot', 'Bitrix24', 'Python']

    # Free audit CTA on p6
    free_map = {
        'ru': {'free_audit_title': 'Начните с бесплатного аудита', 'free_audit_sub': 'Разбираем процессы, находим точки роста — за 30 минут.', 'free_label': 'Бесплатно'},
        'en': {'free_audit_title': 'Start with a free audit', 'free_audit_sub': 'We map your processes and find growth points — in 30 minutes.', 'free_label': 'Free'},
        'ro': {'free_audit_title': 'Începe cu un audit gratuit', 'free_audit_sub': 'Cartografiem procesele și găsim puncte de creștere — în 30 de minute.', 'free_label': 'Gratuit'},
    }
    ctx.update(free_map[lang])

    # Case column headers
    col_map = {
        'ru': {'col_type': 'Тип бизнеса', 'col_now': 'Сейчас', 'col_auto': 'Что автоматизируем', 'col_effect': 'Эффект'},
        'en': {'col_type': 'Business type', 'col_now': 'Current state', 'col_auto': 'What we automate', 'col_effect': 'Result'},
        'ro': {'col_type': 'Tip afacere', 'col_now': 'Situație actuală', 'col_auto': 'Ce automatizăm', 'col_effect': 'Efect'},
    }
    ctx.update(col_map[lang])

    # Popular label for pricing
    popular_map = {'ru': '★ Популярный', 'en': '★ Popular', 'ro': '★ Popular'}
    ctx['popular_label'] = popular_map[lang]

    return ctx


def main():
    parser = argparse.ArgumentParser(description='Generate Aucta AI PDF offer')
    parser.add_argument('--lang', choices=['ru', 'en', 'ro'], default='ru')
    parser.add_argument('--output', help='Output PDF path (default: offer-LANG.pdf)')
    args = parser.parse_args()

    lang = args.lang
    output = args.output or f'offer-{lang}.pdf'

    # Check jinja2
    try:
        import jinja2
    except ImportError:
        print("Installing Jinja2...")
        os.system(f'{sys.executable} -m pip install jinja2 --break-system-packages -q')
        import jinja2

    # Load texts
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, 'texts.json'), 'r', encoding='utf-8') as f:
        texts = json.load(f)

    # Load HTML template
    with open(os.path.join(script_dir, 'offer.html'), 'r', encoding='utf-8') as f:
        html_template = f.read()

    # Build context and render
    ctx = build_context(lang, texts)
    rendered_html = render_template(html_template, ctx)

    # Write rendered HTML for debugging
    debug_html = os.path.join(script_dir, f'offer-{lang}-debug.html')
    with open(debug_html, 'w', encoding='utf-8') as f:
        f.write(rendered_html)
    print(f"Debug HTML: {debug_html}")

    # Generate PDF
    print(f"Generating {output}...")
    import weasyprint
    pdf_path = os.path.join(script_dir, output)
    weasyprint.HTML(
        string=rendered_html,
        base_url=script_dir
    ).write_pdf(pdf_path)

    size = os.path.getsize(pdf_path)
    print(f"Done: {pdf_path} ({size:,} bytes / {size//1024} KB)")


if __name__ == '__main__':
    main()
