#!/usr/bin/env node
/**
 * CyberCampus CTF — Générateur de rapport de sécurité Word
 * Usage : node gen_security_report.js input.json output.docx
 */

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  VerticalAlign, PageBreak, PageNumber, Header, Footer,
  NumberFormat, LevelFormat,
} = require('docx');
const fs = require('fs');

// ── Lecture des arguments ──────────────────────────────────────────
const [,, jsonPath, outPath] = process.argv;
if (!jsonPath || !outPath) {
  console.error('Usage: node gen_security_report.js input.json output.docx');
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));

// ── Couleurs palette sombre → claire pour Word ─────────────────────
const C = {
  darkBg:   '0D1117',
  accent:   '00C896',   // vert CTF (proche de #00f5c0)
  red:      'DC2626',
  orange:   'D97706',
  blue:     '2563EB',
  purple:   '7C3AED',
  gray:     '94A3B8',
  white:    'FFFFFF',
  lightBg:  'F1F5F9',
  midGray:  'CBD5E1',
  darkText: '1E293B',
  border:   'CBD5E1',
};

// ── Helpers ────────────────────────────────────────────────────────
const bord = { style: BorderStyle.SINGLE, size: 1, color: C.border };
const borders = { top: bord, bottom: bord, left: bord, right: bord };

function cell(text, opts = {}) {
  const {
    bold = false, color = C.darkText, bg = null, width = 2340,
    align = AlignmentType.LEFT, italic = false, size = 18,
  } = opts;
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: bg ? { fill: bg, type: ShadingType.CLEAR } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    verticalAlign: VerticalAlign.CENTER,
    children: [
      new Paragraph({
        alignment: align,
        children: [new TextRun({ text: String(text), bold, color, italic, size, font: 'Arial' })],
      }),
    ],
  });
}

function hCell(text, width = 2340) {
  return cell(text, { bold: true, color: C.white, bg: C.darkBg, width });
}

function para(text, opts = {}) {
  const {
    bold = false, color = C.darkText, size = 22, heading = null,
    spaceBefore = 0, spaceAfter = 120, italic = false, align = AlignmentType.LEFT,
  } = opts;
  const p = new Paragraph({
    heading: heading || undefined,
    alignment: align,
    spacing: { before: spaceBefore, after: spaceAfter },
    children: [new TextRun({ text, bold, color, size, italic, font: 'Arial' })],
  });
  return p;
}

function sectionTitle(text) {
  return new Paragraph({
    spacing: { before: 360, after: 180 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.accent } },
    children: [new TextRun({ text, bold: true, size: 28, color: C.darkBg, font: 'Arial' })],
  });
}

function badge(text, color) {
  return new TextRun({ text: `  ${text}  `, bold: true, color: C.white, size: 16,
    highlight: undefined, font: 'Arial' });
}

function typeLabel(t) {
  const map = {
    login_success:      '✅ Connexion réussie',
    login_fail:         '❌ Échec connexion',
    register:           '📝 Inscription',
    flag_submit_ok:     '🚩 Flag validé',
    flag_submit_fail:   '🚩 Flag échoué',
    bruteforce_suspect: '🚨 Brute-force',
    banned_user_attempt:'🔨 Banni tenté',
    rate_limit_hit:     '⏱️ Rate limit',
  };
  return map[t] || t;
}

function riskColor(type) {
  if (['login_fail', 'bruteforce_suspect', 'banned_user_attempt'].includes(type)) return C.red;
  if (['flag_submit_fail', 'rate_limit_hit'].includes(type)) return C.orange;
  if (['login_success', 'flag_submit_ok'].includes(type)) return C.accent;
  return C.blue;
}

// ── Construction du document ───────────────────────────────────────
const sections = [];
const children = [];

// ── Page de garde ──────────────────────────────────────────────────
children.push(
  new Paragraph({ spacing: { before: 1440, after: 0 }, children: [] }),

  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 240 },
    children: [new TextRun({ text: 'CYBERCAMPUS CTF', bold: true, size: 52,
      color: C.accent, font: 'Arial' })],
  }),

  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 480 },
    children: [new TextRun({ text: 'RAPPORT DE SÉCURITÉ', bold: true, size: 36,
      color: C.darkBg, font: 'Arial' })],
  }),

  // Ligne décorative
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 480 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: C.accent } },
    children: [new TextRun({ text: '', size: 4 })],
  }),

  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 120 },
    children: [new TextRun({ text: `Généré le : ${data.generated_at}`, size: 22,
      color: C.gray, font: 'Arial' })],
  }),

  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 720 },
    children: [new TextRun({ text: `Par : ${data.generated_by}`, size: 22,
      color: C.gray, font: 'Arial' })],
  }),

  // Saut de page
  new Paragraph({
    children: [new TextRun({ break: 1 })],
  }),
);

// ── Résumé statistiques ────────────────────────────────────────────
if (data.include_stats && data.stats) {
  const s = data.stats;
  children.push(
    sectionTitle('1. Résumé des 24 dernières heures'),
    para('Vue d\'ensemble de l\'activité de sécurité détectée sur la plateforme.', { color: C.gray, size: 20 }),
    new Paragraph({ spacing: { before: 180, after: 0 }, children: [] }),
  );

  // Tableau stats
  const statRows = [
    ['Événements totaux (24h)', s.events_24h, C.blue],
    ['Connexions réussies',     s.logins_ok_24h, C.accent],
    ['Échecs de connexion',     s.logins_fail_24h, C.red],
    ['Flags validés',           s.flags_ok_24h, C.accent],
    ['Flags échoués',           s.flags_fail_24h, C.orange],
    ['IPs suspectes (5 min)',   s.suspicious_ips.length, s.suspicious_ips.length > 0 ? C.red : C.accent],
  ];

  children.push(new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [5760, 1800, 1800],
    rows: [
      new TableRow({
        children: [hCell('Indicateur', 5760), hCell('Valeur', 1800), hCell('Statut', 1800)],
        tableHeader: true,
      }),
      ...statRows.map(([label, val, col]) => new TableRow({
        children: [
          cell(label, { width: 5760 }),
          cell(val, { width: 1800, bold: true, color: col, align: AlignmentType.CENTER }),
          cell(val > 0 && col === C.red ? '⚠️ Attention' : val > 0 ? '✓ Normal' : '✓ OK',
            { width: 1800, color: col === C.red ? C.red : C.accent, align: AlignmentType.CENTER }),
        ],
      })),
    ],
  }));

  // IPs suspectes si présentes
  if (s.suspicious_ips && s.suspicious_ips.length > 0) {
    children.push(
      new Paragraph({ spacing: { before: 360, after: 120 }, children: [
        new TextRun({ text: '⚠️ IPs suspectes — Brute-force détecté', bold: true,
          size: 24, color: C.red, font: 'Arial' }),
      ]}),
      new Table({
        width: { size: 9360, type: WidthType.DXA },
        columnWidths: [5760, 3600],
        rows: [
          new TableRow({
            children: [hCell('Adresse IP', 5760), hCell('Tentatives (5 min)', 3600)],
            tableHeader: true,
          }),
          ...s.suspicious_ips.map(([ip, cnt]) => new TableRow({
            children: [
              cell(ip, { width: 5760, color: C.purple }),
              cell(cnt + ' tentatives', { width: 3600, bold: true, color: C.red, align: AlignmentType.CENTER }),
            ],
          })),
        ],
      }),
    );
  }

  children.push(new Paragraph({
    children: [new TextRun({ break: 1 })],
  }));
}

// ── IPs bannies ────────────────────────────────────────────────────
if (data.include_banned && data.banned_ips.length > 0) {
  children.push(sectionTitle('2. IPs bannies'));
  children.push(new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [2880, 4080, 2400],
    rows: [
      new TableRow({
        children: [hCell('Adresse IP', 2880), hCell('Raison', 4080), hCell('Bannie le', 2400)],
        tableHeader: true,
      }),
      ...data.banned_ips.map(b => new TableRow({
        children: [
          cell(b.ip, { width: 2880, color: C.red }),
          cell(b.reason || 'Non précisée', { width: 4080 }),
          cell(b.at, { width: 2400, color: C.gray }),
        ],
      })),
    ],
  }));
  children.push(new Paragraph({ spacing: { before: 240, after: 0 }, children: [] }));
  children.push(new Paragraph({ children: [new TextRun({ break: 1 })] }));
}

// ── Journal des événements ─────────────────────────────────────────
if (data.events.length > 0) {
  const sectionNum = (data.include_stats ? 1 : 0) + (data.include_banned && data.banned_ips.length > 0 ? 1 : 0) + 1;
  children.push(sectionTitle(`${sectionNum}. Journal des événements (${data.events.length} entrées)`));
  children.push(para(
    `Export limité aux ${data.events.length} événements les plus récents correspondant aux filtres sélectionnés.`,
    { color: C.gray, size: 18, spaceAfter: 180 }
  ));

  // Regrouper par tranches de 50 pour lisibilité
  const CHUNK = 50;
  for (let i = 0; i < data.events.length; i += CHUNK) {
    const chunk = data.events.slice(i, i + CHUNK);

    if (i > 0) {
      children.push(new Paragraph({
        spacing: { before: 240, after: 120 },
        children: [new TextRun({ text: `Suite (${i + 1} – ${Math.min(i + CHUNK, data.events.length)})`,
          bold: true, size: 20, color: C.gray, font: 'Arial' })],
      }));
    }

    children.push(new Table({
      width: { size: 9360, type: WidthType.DXA },
      columnWidths: [1440, 1800, 1200, 1200, 1440, 2280],
      rows: [
        new TableRow({
          children: [
            hCell('Date/Heure', 1440),
            hCell('Type', 1800),
            hCell('IP', 1200),
            hCell('Utilisateur', 1200),
            hCell('Chemin', 1440),
            hCell('Détails', 2280),
          ],
          tableHeader: true,
        }),
        ...chunk.map((ev, idx) => new TableRow({
          children: [
            cell(ev.ts, { width: 1440, size: 16, color: C.gray }),
            cell(typeLabel(ev.type), { width: 1800, size: 16, bold: true, color: riskColor(ev.type) }),
            cell(ev.ip, { width: 1200, size: 16, color: C.purple }),
            cell(ev.user, { width: 1200, size: 16 }),
            cell(ev.path.length > 20 ? ev.path.substring(0, 20) + '…' : ev.path, { width: 1440, size: 14, color: C.gray }),
            cell(ev.extra ? ev.extra.substring(0, 50) : '—', { width: 2280, size: 14, color: C.gray }),
          ],
        })),
      ],
    }));

    if (i + CHUNK < data.events.length) {
      children.push(new Paragraph({ children: [new TextRun({ break: 1 })] }));
    }
  }
}

// ── Footer ─────────────────────────────────────────────────────────
const footerContent = new Footer({
  children: [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      border: { top: { style: BorderStyle.SINGLE, size: 2, color: C.border } },
      spacing: { before: 120 },
      children: [
        new TextRun({ text: `CyberCampus CTF — Rapport de sécurité — ${data.generated_at}`,
          size: 16, color: C.gray, font: 'Arial' }),
      ],
    }),
  ],
});

// ── Assemblage final ───────────────────────────────────────────────
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: 'Arial', size: 22, color: C.darkText } },
    },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 },
      },
    },
    footers: { default: footerContent },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log(`OK: ${outPath}`);
}).catch(err => {
  console.error(err);
  process.exit(1);
});