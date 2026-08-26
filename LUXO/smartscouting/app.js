/* El arranque (al final del archivo) valida la sesion contra la base de datos
   y deja aqui el perfil, la configuracion y las cotizaciones ya cargadas. */
const PERFIL = () => window.__perfil || { nombre: '', apellidos: '', rol: 'scouting', id: null };
const ES_ADMIN = () => PERFIL().rol === 'admin';

const {
  useState,
  useMemo,
  useEffect,
  useCallback
} = React;
const RS = new Proxy(window.Recharts || {}, {
  get: (t, p) => t[p] || (() => null)
});
const {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} = RS;
const LS = new Proxy(window.LucideReact || window.lucide || {}, {
  get: (t, p) => t[p] || (() => null)
});
const {
  Archive,
  Award,
  CheckSquare,
  ChevronDown,
  ChevronRight,
  DollarSign,
  Download,
  Edit3,
  Home,
  LayoutDashboard,
  Moon,
  Package,
  Plus,
  RefreshCw,
  Save,
  Search,
  Settings,
  SortAsc,
  SortDesc,
  Square,
  Sun,
  Tags,
  Trash2,
  TrendingUp,
  Upload,
  X,
  Zap,
  AlertCircle,
  Truck,
  Building2,
  Star,
  LogOut,
  Filter,
  SlidersHorizontal,
  LayoutGrid,
  ArrowLeft
} = LS;
const fmt = v => new Intl.NumberFormat('es-MX', {
  style: 'currency',
  currency: 'MXN',
  minimumFractionDigits: 2
}).format(v || 0);
const fmtN = v => new Intl.NumberFormat('es-MX', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2
}).format(v || 0);
const fmtPct = v => Number(v || 0).toFixed(2) + '%';
const eq = (a, b) => Math.abs((a || 0) - (b || 0)) < 0.005;
const cn = v => {
  if (v === undefined || v === null || v === '') return 0;
  if (typeof v === 'number') return v;
  const n = parseFloat(v.toString().replace(/[$,%]/g, '').replace(/,/g, ''));
  return isNaN(n) ? 0 : n;
};
const loadXLSX = () => Promise.resolve(window.XLSX);
const PI = {
  ml: {
    name: 'Mercado Libre',
    logo: 'ML',
    color: '#FACC15'
  },
  amz: {
    name: 'Amazon',
    logo: 'A',
    color: '#F97316'
  },
  wal: {
    name: 'Walmart',
    logo: 'W',
    color: '#3B82F6'
  }
};
const PC = {
  'ML': '#FACC15',
  'AMZ': '#F97316',
  'WAL': '#3B82F6'
};
function GaugeBar({
  pct
}) {
  const w = Math.min(Math.max(pct, 0), 100);
  const col = pct < 0 ? 'var(--danger)' : pct < 15 ? 'var(--warn)' : 'var(--accent)';
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6,
      marginBottom: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "gt"
  }, /*#__PURE__*/React.createElement("div", {
    className: "gf",
    style: {
      width: w + '%',
      background: col
    }
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      fontFamily: 'var(--mono)',
      fontWeight: 600,
      minWidth: 40,
      textAlign: 'right',
      color: col
    }
  }, fmtPct(pct)));
}
function PlatCard({
  id,
  name,
  logo,
  color,
  res,
  mlType,
  onMLTypeChange,
  onPChange,
  showMLToggle
}) {
  const isWin = res._win,
    isLos = res.profit < 0;
  return /*#__PURE__*/React.createElement("div", {
    className: `pc${isWin ? ' win' : isLos ? ' los' : ''}`
  }, /*#__PURE__*/React.createElement("div", {
    className: "ph"
  }, /*#__PURE__*/React.createElement("div", {
    className: "pl",
    style: {
      background: color + '22',
      color
    }
  }, logo), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: 'var(--t1)'
    }
  }, name), isWin && !isLos && /*#__PURE__*/React.createElement("span", {
    className: "badge b-win"
  }, "★ Mejor margen"), isLos && /*#__PURE__*/React.createElement("span", {
    className: "badge b-los"
  }, "Pérdida"), !isWin && !isLos && res._low && /*#__PURE__*/React.createElement("span", {
    className: "badge b-low"
  }, "Menor margen")), showMLToggle && /*#__PURE__*/React.createElement("div", {
    className: "mts"
  }, /*#__PURE__*/React.createElement("button", {
    className: 'mtb' + (mlType === 'CLASICA' ? ' on' : ''),
    onClick: () => onMLTypeChange('CLASICA')
  }, "Clásica"), /*#__PURE__*/React.createElement("button", {
    className: 'mtb' + (mlType === 'PREMIUM' ? ' on' : ''),
    onClick: () => onMLTypeChange('PREMIUM')
  }, "Premium"))), /*#__PURE__*/React.createElement("div", {
    className: "pb"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 4,
      fontSize: 10,
      color: 'var(--t3)',
      textTransform: 'uppercase',
      letterSpacing: '.05em'
    }
  }, "Utilidad neta"), /*#__PURE__*/React.createElement("div", {
    className: "bn",
    style: {
      color: res.profit >= 0 ? 'var(--accent)' : 'var(--danger)',
      marginBottom: 6
    }
  }, fmt(res.profit)), /*#__PURE__*/React.createElement(GaugeBar, {
    pct: res.margin
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "lbl",
    style: {
      marginBottom: 4
    }
  }, "Precio de venta (MXN)"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      background: 'var(--s2)',
      border: '0.5px solid var(--border-s)',
      borderRadius: 'var(--r)',
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "fpre"
  }, "$"), /*#__PURE__*/React.createElement("input", {
    type: "number",
    value: Math.round(res.price || 0),
    onChange: e => onPChange(Number(e.target.value)),
    style: {
      flex: 1,
      border: 'none',
      background: 'transparent',
      padding: '0 10px',
      height: 34,
      fontSize: 13,
      color: 'var(--t1)',
      outline: 'none',
      minWidth: 0,
      width: 0,
      fontFamily: 'var(--mono)',
      textAlign: 'center'
    }
  }), /*#__PURE__*/React.createElement("span", {
    className: "fsuf",
    style: {
      fontSize: 11
    }
  }, "MXN"))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "fr"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fl"
  }, "Comisión (", fmtPct(res.baseComPerc), ")"), /*#__PURE__*/React.createElement("span", {
    className: "fv neg"
  }, "−", fmt(res.baseCommAmt))), res.discAmt > 0 && /*#__PURE__*/React.createElement("div", {
    className: "fr"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fl",
    style: {
      color: 'var(--accent)'
    }
  }, "Desc. plataforma"), /*#__PURE__*/React.createElement("span", {
    className: "fv pos"
  }, "+", fmt(res.discAmt))), res.msiAmt > 0 && /*#__PURE__*/React.createElement("div", {
    className: "fr"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fl"
  }, "MSI (", fmtPct(res.extraPerc || 0), ")"), /*#__PURE__*/React.createElement("span", {
    className: "fv neg"
  }, "−", fmt(res.msiAmt))), /*#__PURE__*/React.createElement("div", {
    className: "fr"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fl"
  }, "Envío"), /*#__PURE__*/React.createElement("span", {
    className: "fv neg"
  }, "−", fmt(res.ship))), /*#__PURE__*/React.createElement("div", {
    className: "fr"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fl"
  }, "Retención (", fmtPct(res.taxPerc), ")"), /*#__PURE__*/React.createElement("span", {
    className: "fv neg"
  }, "−", fmt(res.taxAmt))), /*#__PURE__*/React.createElement("div", {
    className: "fr"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fl"
  }, "Factor REFI"), /*#__PURE__*/React.createElement("span", {
    className: "fv"
  }, "×", res.factor)), /*#__PURE__*/React.createElement("div", {
  className: 'res-box' + (!(res.price > 0) ? ' idle' : res.margin < 0 ? ' neg' : '')
}, /*#__PURE__*/React.createElement("div", {
  className: "res-main"
}, /*#__PURE__*/React.createElement("span", {
  className: "res-lbl"
}, "Margen neto"), /*#__PURE__*/React.createElement("span", {
  className: "res-num"
}, res.price > 0 ? fmtPct(res.margin) : '—')), /*#__PURE__*/React.createElement("div", {
  className: "res-sub"
}, /*#__PURE__*/React.createElement("span", {
  className: "res-sub-l"
}, "ROI sobre costo"), /*#__PURE__*/React.createElement("span", {
  className: 'res-sub-v' + (res.price > 0 && res.roi < 0 ? ' neg' : '')
}, res.price > 0 ? fmtPct(res.roi) : '—'))))));
}

/* ─── DASHBOARD ─────────────────────────────────────────────────────────────── */
function Dashboard({
  quotes,
  onLoad,
  onDelete
}) {
  const [dF, setDF] = useState('all');
  const [dC, setDC] = useState('all');
  const [dP, setDP] = useState('all');
  const [selected, setSelected] = useState(new Set());
  const cats = useMemo(() => ['all', ...[...new Set(quotes.map(q => q.category))].sort()], [quotes]);
  const provs = useMemo(() => ['all', ...[...new Set(quotes.map(q => q.supplier).filter(Boolean))].sort()], [quotes]);
  const filtered = useMemo(() => {
    let q = quotes;
    if (dF === 'rentable') q = q.filter(x => x.fullResults.ml.profit > 0 || x.fullResults.amz.profit > 0 || x.fullResults.wal.profit > 0);
    if (dF === 'perdida') q = q.filter(x => x.fullResults.ml.profit < 0 && x.fullResults.amz.profit < 0 && x.fullResults.wal.profit < 0);
    if (dC !== 'all') q = q.filter(x => x.category === dC);
    if (dP !== 'all') q = q.filter(x => x.supplier === dP);
    return q;
  }, [quotes, dF, dC, dP]);
  const catData = useMemo(() => {
    const g = {};
    filtered.forEach(q => {
      if (!g[q.category]) g[q.category] = {
        cat: q.category,
        count: 0,
        avgMargin: 0,
        totalProfit: 0
      };
      g[q.category].count++;
      g[q.category].totalProfit += Math.max(q.fullResults.ml.profit, q.fullResults.amz.profit, q.fullResults.wal.profit);
      g[q.category].avgMargin += Math.max(q.fullResults.ml.margin, q.fullResults.amz.margin, q.fullResults.wal.margin);
    });
    return Object.values(g).map(c => ({
      ...c,
      avgMargin: c.avgMargin / c.count
    })).sort((a, b) => b.totalProfit - a.totalProfit).slice(0, 8);
  }, [filtered]);
  if (quotes.length === 0) return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '80px 24px',
      gap: 16,
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 64,
      height: 64,
      borderRadius: 16,
      background: 'var(--s2)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement(LayoutDashboard, {
    size: 28,
    color: "var(--t4)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 16,
      fontWeight: 700,
      color: 'var(--t2)'
    }
  }, "Sin datos aún"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--t3)',
      maxWidth: 320
    }
  }, "Guarda escenarios desde la calculadora o carga un Excel para ver el dashboard."));
  const bPC = {
    ML: 0,
    AMZ: 0,
    WAL: 0
  };
  filtered.forEach(q => {
    if (q.bestPlatform && bPC[q.bestPlatform] !== undefined) bPC[q.bestPlatform]++;
  });
  const dom = Object.entries(bPC).reduce((a, b) => b[1] > a[1] ? b : a)[0];
  const aML = filtered.length ? filtered.reduce((s, q) => s + q.fullResults.ml.margin, 0) / filtered.length : 0;
  const aAMZ = filtered.length ? filtered.reduce((s, q) => s + q.fullResults.amz.margin, 0) / filtered.length : 0;
  const aWAL = filtered.length ? filtered.reduce((s, q) => s + q.fullResults.wal.margin, 0) / filtered.length : 0;
  const tML = filtered.reduce((s, q) => s + q.fullResults.ml.profit, 0);
  const tAMZ = filtered.reduce((s, q) => s + q.fullResults.amz.profit, 0);
  const tWAL = filtered.reduce((s, q) => s + q.fullResults.wal.profit, 0);
  const rent = filtered.filter(q => q.fullResults.ml.profit > 0 || q.fullResults.amz.profit > 0 || q.fullResults.wal.profit > 0).length;
  const Tip = ({
    active,
    payload,
    label
  }) => {
    if (!active || !payload?.length) return null;
    return /*#__PURE__*/React.createElement("div", {
      style: {
        background: 'var(--s1)',
        border: '0.5px solid var(--border-s)',
        borderRadius: 8,
        padding: '10px 14px'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        fontWeight: 700,
        color: 'var(--t2)',
        marginBottom: 6
      }
    }, label), payload.map((p, i) => /*#__PURE__*/React.createElement("div", {
      key: i,
      style: {
        fontSize: 11,
        color: p.color || 'var(--t1)',
        marginBottom: 2
      }
    }, p.name, ": ", /*#__PURE__*/React.createElement("strong", null, fmtN(p.value)))));
  };

  // Plataforma cards — siempre funcionan
  const platCards = [{
    key: 'ml',
    name: 'Mercado Libre',
    color: '#FACC15',
    margin: aML,
    profit: tML,
    count: bPC.ML
  }, {
    key: 'amz',
    name: 'Amazon',
    color: '#F97316',
    margin: aAMZ,
    profit: tAMZ,
    count: bPC.AMZ
  }, {
    key: 'wal',
    name: 'Walmart',
    color: '#3B82F6',
    margin: aWAL,
    profit: tWAL,
    count: bPC.WAL
  }];
  const maxMargin = Math.max(aML, aAMZ, aWAL);

  // selección masiva
  const allIds = filtered.map(q => q.id);
  const allSel = allIds.length > 0 && allIds.every(id => selected.has(id));
  const toggleAll = () => {
    if (allSel) {
      const n = new Set(selected);
      allIds.forEach(id => n.delete(id));
      setSelected(n);
    } else {
      const n = new Set(selected);
      allIds.forEach(id => n.add(id));
      setSelected(n);
    }
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 24px 80px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "toolbar"
  }, /*#__PURE__*/React.createElement("div", {
    className: "tb-sec"
  }, /*#__PURE__*/React.createElement("div", {
    className: "tb-sec-hd"
  }, /*#__PURE__*/React.createElement(SlidersHorizontal, {
    size: 11
  }), "Filtrar"), /*#__PURE__*/React.createElement("div", {
    className: "tb-row"
  }, /*#__PURE__*/React.createElement("div", {
    className: "tb-field"
  }, /*#__PURE__*/React.createElement("label", null, "Resultado"), /*#__PURE__*/React.createElement("div", {
    className: "seg-sm"
  }, [['all', 'Todos'], ['rentable', 'Rentables'], ['perdida', 'Con pérdida']].map(([v, l]) => /*#__PURE__*/React.createElement("button", {
    key: v,
    className: dF === v ? 'on' : '',
    onClick: () => setDF(v)
  }, l)))), /*#__PURE__*/React.createElement("div", {
    className: "tb-field"
  }, /*#__PURE__*/React.createElement("label", null, "Categoría"), /*#__PURE__*/React.createElement("select", {
    className: "sel",
    style: {
      height: 34,
      width: 160,
      fontSize: 11
    },
    value: dC,
    onChange: e => setDC(e.target.value)
  }, /*#__PURE__*/React.createElement("option", {
    value: "all"
  }, "Todas"), cats.filter(c => c !== 'all').map(c => /*#__PURE__*/React.createElement("option", {
    key: c,
    value: c
  }, c)))), provs.length > 1 && /*#__PURE__*/React.createElement("div", {
    className: "tb-field"
  }, /*#__PURE__*/React.createElement("label", null, "Proveedor"), /*#__PURE__*/React.createElement("select", {
    className: "sel",
    style: {
      height: 34,
      width: 160,
      fontSize: 11
    },
    value: dP,
    onChange: e => setDP(e.target.value)
  }, /*#__PURE__*/React.createElement("option", {
    value: "all"
  }, "Todos"), provs.filter(p => p !== 'all').map(p => /*#__PURE__*/React.createElement("option", {
    key: p,
    value: p
  }, p)))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginLeft: 'auto',
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      paddingBottom: 2
    }
  }, (dF !== 'all' || dC !== 'all' || dP !== 'all') && /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    style: {
      height: 30,
      padding: '0 10px',
      fontSize: 10
    },
    onClick: () => {
      setDF('all');
      setDC('all');
      setDP('all');
    }
  }, /*#__PURE__*/React.createElement(RefreshCw, {
    size: 11
  }), "Limpiar"), /*#__PURE__*/React.createElement("span", {
    className: "res-count"
  }, /*#__PURE__*/React.createElement("strong", null, filtered.length), " productos"))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: 'repeat(5,1fr)',
      gap: 10,
      marginBottom: 14
    }
  }, [{
    lbl: 'Productos',
    val: filtered.length,
    sub: `${rent} rentables`,
    col: 'var(--accent)',
    ic: /*#__PURE__*/React.createElement(Package, {
      size: 15
    })
  }, {
    lbl: 'Plataforma líder',
    val: dom,
    sub: `${bPC[dom]} de ${filtered.length}`,
    col: PC[dom],
    ic: /*#__PURE__*/React.createElement(Award, {
      size: 15
    })
  }, {
    lbl: 'Margen prom. ML',
    val: fmtPct(aML),
    sub: 'Mercado Libre',
    col: '#FACC15',
    ic: /*#__PURE__*/React.createElement(TrendingUp, {
      size: 15
    })
  }, {
    lbl: 'Margen prom. AMZ',
    val: fmtPct(aAMZ),
    sub: 'Amazon',
    col: '#F97316',
    ic: /*#__PURE__*/React.createElement(TrendingUp, {
      size: 15
    })
  }, {
    lbl: 'Margen prom. WMT',
    val: fmtPct(aWAL),
    sub: 'Walmart',
    col: '#3B82F6',
    ic: /*#__PURE__*/React.createElement(TrendingUp, {
      size: 15
    })
  }].map((k, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "kpi-card"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 10,
      fontWeight: 600,
      color: 'var(--t3)',
      textTransform: 'uppercase',
      letterSpacing: '.05em'
    }
  }, k.lbl), /*#__PURE__*/React.createElement("span", {
    style: {
      color: k.col,
      opacity: .7
    }
  }, k.ic)), /*#__PURE__*/React.createElement("div", {
    className: "kpi-val",
    style: {
      color: k.col
    }
  }, k.val), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--t3)'
    }
  }, k.sub)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr 1fr',
      gap: 10,
      marginBottom: 14
    }
  }, platCards.map(p => {
    const barW = maxMargin > 0 ? Math.max(p.margin / maxMargin * 100, 0) : 0;
    const isLead = p.key.toUpperCase() === dom || p.key === 'ml' && dom === 'ML' || p.key === 'amz' && dom === 'AMZ' || p.key === 'wal' && dom === 'WAL';
    return /*#__PURE__*/React.createElement("div", {
      key: p.key,
      className: "card",
      style: {
        padding: '14px 16px',
        borderColor: isLead ? p.color + '55' : 'var(--border)'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 10
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 8
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        width: 24,
        height: 24,
        borderRadius: 5,
        background: p.color + '22',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 10,
        fontWeight: 800,
        color: p.color
      }
    }, p.key === 'ml' ? 'ML' : p.key === 'amz' ? 'A' : 'W'), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 12,
        fontWeight: 600,
        color: 'var(--t1)'
      }
    }, p.name)), isLead && /*#__PURE__*/React.createElement("span", {
      className: "badge b-win"
    }, "Líder")), /*#__PURE__*/React.createElement("div", {
      style: {
        marginBottom: 8
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: 4
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10,
        color: 'var(--t3)',
        textTransform: 'uppercase',
        letterSpacing: '.04em'
      }
    }, "Margen prom."), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 14,
        fontWeight: 700,
        fontFamily: 'var(--mono)',
        color: p.margin >= 0 ? p.color : 'var(--danger)'
      }
    }, fmtPct(p.margin))), /*#__PURE__*/React.createElement("div", {
      style: {
        height: 4,
        background: 'var(--s3)',
        borderRadius: 99,
        overflow: 'hidden'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        height: '100%',
        width: barW + '%',
        background: p.color,
        borderRadius: 99,
        transition: 'width .4s ease'
      }
    }))), /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 8,
        paddingTop: 8,
        borderTop: '0.5px solid var(--border)'
      }
    }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 9,
        color: 'var(--t3)',
        textTransform: 'uppercase',
        letterSpacing: '.04em',
        marginBottom: 2
      }
    }, "Utilidad total"), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 12,
        fontWeight: 700,
        fontFamily: 'var(--mono)',
        color: p.profit >= 0 ? 'var(--t1)' : 'var(--danger)'
      }
    }, fmt(p.profit))), /*#__PURE__*/React.createElement("div", {
      style: {
        textAlign: 'right'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 9,
        color: 'var(--t3)',
        textTransform: 'uppercase',
        letterSpacing: '.04em',
        marginBottom: 2
      }
    }, "Mejor canal"), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 12,
        fontWeight: 700,
        fontFamily: 'var(--mono)',
        color: 'var(--t2)'
      }
    }, p.count, " prod."))));
  })), catData.length >= 2 ? /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 12,
      marginBottom: 14
    }
  }, [{
    ttl: 'Utilidad total por categoría',
    key: 'totalProfit',
    col: 'var(--accent)',
    fmtV: v => '$' + Math.round(v / 1000) + 'k'
  }, {
    ttl: 'Margen promedio por categoría',
    key: 'avgMargin',
    col: '#7C3AED',
    fmtV: v => v.toFixed(1) + '%'
  }].map(c => /*#__PURE__*/React.createElement("div", {
    key: c.key,
    className: "card",
    style: {
      padding: '16px 20px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "sec-ttl"
  }, c.ttl), /*#__PURE__*/React.createElement(ResponsiveContainer, {
    width: "100%",
    height: Math.max(catData.length * 32 + 20, 120)
  }, /*#__PURE__*/React.createElement(BarChart, {
    data: catData,
    layout: "vertical",
    barCategoryGap: "25%",
    margin: {
      left: 0,
      right: 20,
      top: 0,
      bottom: 0
    }
  }, /*#__PURE__*/React.createElement(CartesianGrid, {
    strokeDasharray: "3 3",
    stroke: "rgba(128,128,128,0.1)",
    horizontal: false
  }), /*#__PURE__*/React.createElement(XAxis, {
    type: "number",
    tick: {
      fontSize: 10,
      fill: 'var(--t3)'
    },
    axisLine: false,
    tickLine: false,
    tickFormatter: c.fmtV
  }), /*#__PURE__*/React.createElement(YAxis, {
    type: "category",
    dataKey: "cat",
    tick: {
      fontSize: 10,
      fill: 'var(--t3)',
      fontFamily: 'var(--sans)'
    },
    axisLine: false,
    tickLine: false,
    width: 95
  }), /*#__PURE__*/React.createElement(Tooltip, {
    content: /*#__PURE__*/React.createElement(Tip, null)
  }), /*#__PURE__*/React.createElement(Bar, {
    dataKey: c.key,
    name: c.ttl,
    fill: c.col,
    fillOpacity: 0.75,
    radius: [0, 4, 4, 0]
  })))))) : catData.length === 1 ? /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      padding: '14px 16px',
      marginBottom: 14,
      display: 'flex',
      alignItems: 'center',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 36,
      height: 36,
      borderRadius: 8,
      background: 'var(--ac-dim)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement(Tags, {
    size: 16,
    color: "var(--accent)"
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontWeight: 600,
      color: 'var(--t1)',
      marginBottom: 2
    }
  }, "Categoría única: ", catData[0].cat), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--t3)'
    }
  }, "Las gráficas por categoría aparecen cuando tienes cotizaciones en 2 o más categorías distintas."))) : null, /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      padding: '16px 20px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "sec-ttl",
    style: {
      margin: 0
    }
  }, "Todas las cotizaciones · mejor margen"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    style: {
      height: 28,
      padding: '0 10px',
      fontSize: 10
    },
    onClick: toggleAll
  }, allSel ? /*#__PURE__*/React.createElement(CheckSquare, {
    size: 12,
    color: "var(--accent)"
  }) : /*#__PURE__*/React.createElement(Square, {
    size: 12
  }), allSel ? 'Deseleccionar todo' : 'Seleccionar todo'))), /*#__PURE__*/React.createElement("table", {
    className: "tbl"
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: {
      width: 36,
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      background: 'none',
      border: 'none',
      cursor: 'pointer',
      display: 'flex',
      margin: '0 auto'
    },
    onClick: toggleAll
  }, allSel ? /*#__PURE__*/React.createElement(CheckSquare, {
    size: 13,
    color: "var(--accent)"
  }) : /*#__PURE__*/React.createElement(Square, {
    size: 13
  }))), /*#__PURE__*/React.createElement("th", null, "#"), /*#__PURE__*/React.createElement("th", null, "Producto"), /*#__PURE__*/React.createElement("th", null, "Proveedor"), /*#__PURE__*/React.createElement("th", null, "Cat."), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: 'center',
      background: 'rgba(250,204,21,.05)'
    }
  }, "ML"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: 'center',
      background: 'rgba(249,115,22,.05)'
    }
  }, "Amazon"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: 'center',
      background: 'rgba(59,130,246,.05)'
    }
  }, "Walmart"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: 'right'
    }
  }, "Mejor utilidad"))), /*#__PURE__*/React.createElement("tbody", null, [...filtered].sort((a, b) => Math.max(b.fullResults.ml.margin, b.fullResults.amz.margin, b.fullResults.wal.margin) - Math.max(a.fullResults.ml.margin, a.fullResults.amz.margin, a.fullResults.wal.margin)).map((q, i) => {
    const bP = Math.max(q.fullResults.ml.profit, q.fullResults.amz.profit, q.fullResults.wal.profit);
    const bM = Math.max(q.fullResults.ml.margin, q.fullResults.amz.margin, q.fullResults.wal.margin);
    return /*#__PURE__*/React.createElement("tr", {
      key: q.id,
      onDoubleClick: () => onLoad(q),
      style: {
        cursor: 'pointer'
      }
    }, /*#__PURE__*/React.createElement("td", {
      style: {
        textAlign: 'center'
      }
    }, /*#__PURE__*/React.createElement("button", {
      style: {
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        display: 'flex',
        margin: '0 auto'
      },
      onClick: e => {
        e.stopPropagation();
        const n = new Set(selected);
        n.has(q.id) ? n.delete(q.id) : n.add(q.id);
        setSelected(n);
      }
    }, selected.has(q.id) ? /*#__PURE__*/React.createElement(CheckSquare, {
      size: 13,
      color: "var(--accent)"
    }) : /*#__PURE__*/React.createElement(Square, {
      size: 13,
      color: "var(--t4)"
    }))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("span", {
      style: {
        fontWeight: 800,
        fontFamily: 'var(--mono)',
        color: i === 0 ? 'var(--accent)' : 'var(--t3)',
        fontSize: 12
      }
    }, "#", i + 1)), /*#__PURE__*/React.createElement("td", {
      style: {
        maxWidth: 180
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontWeight: 600,
        fontSize: 12,
        color: 'var(--t1)',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis'
      }
    }, q.name)), /*#__PURE__*/React.createElement("td", null, q.supplier ? /*#__PURE__*/React.createElement("span", {
      className: "prov-tag"
    }, /*#__PURE__*/React.createElement(Building2, {
      size: 10
    }), q.supplier) : /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10,
        color: 'var(--t4)'
      }
    }, "—")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("span", {
      className: "badge",
      style: {
        background: 'var(--s2)',
        color: 'var(--t3)',
        border: '0.5px solid var(--border-s)',
        fontSize: 9
      }
    }, q.category)), ['ml', 'amz', 'wal'].map(k => {
      const r = q.fullResults[k];
      return /*#__PURE__*/React.createElement("td", {
        key: k,
        style: {
          textAlign: 'center'
        }
      }, /*#__PURE__*/React.createElement("span", {
        style: {
          fontFamily: 'var(--mono)',
          fontSize: 12,
          fontWeight: 600,
          color: eq(r.margin, bM) ? 'var(--accent)' : r.margin < 0 ? 'var(--danger)' : 'var(--t2)'
        }
      }, fmtPct(r.margin)));
    }), /*#__PURE__*/React.createElement("td", {
      style: {
        textAlign: 'right',
        fontFamily: 'var(--mono)',
        fontSize: 12,
        fontWeight: 700,
        color: 'var(--accent)'
      }
    }, fmt(bP)));
  })))), selected.size > 0 && /*#__PURE__*/React.createElement("div", {
    className: "sel-bar"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(CheckSquare, {
    size: 15,
    color: "var(--accent)"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 700,
      color: 'var(--t1)'
    }
  }, selected.size, " seleccionado", selected.size !== 1 ? 's' : '')), /*#__PURE__*/React.createElement("div", {
    style: {
      width: '0.5px',
      height: 18,
      background: 'var(--border-s)'
    }
  }), /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    style: {
      height: 30,
      fontSize: 11
    },
    onClick: toggleAll
  }, allSel ? 'Deseleccionar todo' : 'Seleccionar todo'), /*#__PURE__*/React.createElement("button", {
    className: "btn bd",
    style: {
      height: 30,
      fontSize: 11
    },
    onClick: () => {
      onDelete(selected);
      setSelected(new Set());
    }
  }, /*#__PURE__*/React.createElement(Trash2, {
    size: 12
  }), "Eliminar ", selected.size), /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    style: {
      height: 30,
      fontSize: 11
    },
    onClick: () => setSelected(new Set())
  }, /*#__PURE__*/React.createElement(X, {
    size: 12
  }), "Limpiar")));
}

/* ─── HISTORIAL ─────────────────────────────────────────────────────────────── */
function History({
  quotes,
  onLoad,
  onDelete
}) {
  const [search, setSearch] = useState('');
  const [catF, setCatF] = useState('all');
  const [platF, setPlatF] = useState('all');
  const [provF, setProvF] = useState('all');
  const [profF, setProfF] = useState('all');
  const [groupBy, setGroupBy] = useState('month');
  const [sortKey, setSortKey] = useState('date');
  const [sortDir, setSortDir] = useState('desc');
  const [expanded, setExpanded] = useState({});
  const [showMore, setShowMore] = useState(false);
  const [selected, setSelected] = useState(new Set());
  const cats = useMemo(() => ['all', ...[...new Set(quotes.map(q => q.category))].sort()], [quotes]);
  const provs = useMemo(() => ['all', ...[...new Set(quotes.map(q => q.supplier).filter(Boolean))].sort()], [quotes]);
  const filtered = useMemo(() => {
    let q = [...quotes];
    if (search) {
      const s = search.toUpperCase();
      q = q.filter(x => x.name && x.name.toUpperCase().includes(s) || x.category && x.category.toUpperCase().includes(s) || x.supplier && x.supplier.toUpperCase().includes(s));
    }
    if (catF !== 'all') q = q.filter(x => x.category === catF);
    if (platF !== 'all') q = q.filter(x => x.bestPlatform === platF);
    if (provF !== 'all') q = q.filter(x => x.supplier === provF);
    if (profF === 'positivo') q = q.filter(x => x.fullResults.ml.profit > 0 || x.fullResults.amz.profit > 0 || x.fullResults.wal.profit > 0);
    if (profF === 'negativo') q = q.filter(x => x.fullResults.ml.profit < 0 && x.fullResults.amz.profit < 0 && x.fullResults.wal.profit < 0);
    const dir = sortDir === 'asc' ? 1 : -1;
    q.sort((a, b) => {
      if (sortKey === 'date') return (a.id - b.id) * dir;
      if (sortKey === 'name') return a.name.localeCompare(b.name) * dir;
      if (sortKey === 'supplier') return (a.supplier || '').localeCompare(b.supplier || '') * dir;
      if (sortKey === 'margin') return (Math.max(a.fullResults.ml.margin, a.fullResults.amz.margin, a.fullResults.wal.margin) - Math.max(b.fullResults.ml.margin, b.fullResults.amz.margin, b.fullResults.wal.margin)) * dir;
      if (sortKey === 'profit') return (Math.max(a.fullResults.ml.profit, a.fullResults.amz.profit, a.fullResults.wal.profit) - Math.max(b.fullResults.ml.profit, b.fullResults.amz.profit, b.fullResults.wal.profit)) * dir;
      if (sortKey === 'cost') return (a.costMXN - b.costMXN) * dir;
      return 0;
    });
    return q;
  }, [quotes, search, catF, platF, provF, profF, sortKey, sortDir]);
  const grouped = useMemo(() => {
    const g = {};
    filtered.forEach(q => {
      let key;
      if (groupBy === 'month') {
        const d = new Date(q.id);
        key = d.toLocaleDateString('es-ES', {
          month: 'long',
          year: 'numeric'
        });
      } else if (groupBy === 'category') key = q.category || 'Sin categoría';else if (groupBy === 'platform') key = {
        ML: 'Mercado Libre',
        AMZ: 'Amazon México',
        WAL: 'Walmart México'
      }[q.bestPlatform] || q.bestPlatform || 'Sin plataforma';else if (groupBy === 'supplier') key = q.supplier || 'Sin proveedor';else key = '__all__';
      if (!g[key]) g[key] = {
        key,
        items: []
      };
      g[key].items.push(q);
    });
    return Object.values(g).sort((a, b) => {
      if (groupBy === 'month') return new Date(b.items[0].id) - new Date(a.items[0].id);
      return a.key === '__all__' ? 0 : a.key.localeCompare(b.key);
    });
  }, [filtered, groupBy]);
  const toggleGroup = k => setExpanded(p => ({
    ...p,
    [k]: p[k] === false
  }));
  const toggleSort = k => {
    if (sortKey === k) setSortDir(d => d === 'asc' ? 'desc' : 'asc');else {
      setSortKey(k);
      setSortDir('desc');
    }
  };
  const SI = ({
    k
  }) => sortKey !== k ? /*#__PURE__*/React.createElement(SortAsc, {
    size: 11,
    style: {
      opacity: .3
    }
  }) : sortDir === 'asc' ? /*#__PURE__*/React.createElement(SortAsc, {
    size: 11
  }) : /*#__PURE__*/React.createElement(SortDesc, {
    size: 11
  });
  const hasFilters = search || catF !== 'all' || platF !== 'all' || provF !== 'all' || profF !== 'all';
  const allFiltered = filtered.map(q => q.id);
  const allSel = allFiltered.length > 0 && allFiltered.every(id => selected.has(id));
  const toggleAll = () => {
    if (allSel) {
      const n = new Set(selected);
      allFiltered.forEach(id => n.delete(id));
      setSelected(n);
    } else {
      const n = new Set(selected);
      allFiltered.forEach(id => n.add(id));
      setSelected(n);
    }
  };
  const exportPDF = () => {
    const selQuotes = filtered.filter(q => selected.has(q.id));
    if (!selQuotes.length) return;
    const date = new Date().toLocaleDateString('es-MX', {
      day: '2-digit',
      month: 'long',
      year: 'numeric'
    });
    const rentCount = selQuotes.filter(q => Math.max(q.fullResults.ml.profit, q.fullResults.amz.profit, q.fullResults.wal.profit) > 0).length;
    const avgBestMargin = selQuotes.reduce((s, q) => s + Math.max(q.fullResults.ml.margin, q.fullResults.amz.margin, q.fullResults.wal.margin), 0) / selQuotes.length;
    const totalBestProfit = selQuotes.reduce((s, q) => s + Math.max(q.fullResults.ml.profit, q.fullResults.amz.profit, q.fullResults.wal.profit), 0);
    const rows = selQuotes.map((q, i) => {
      const bP = Math.max(q.fullResults.ml.profit, q.fullResults.amz.profit, q.fullResults.wal.profit);
      const bM = Math.max(q.fullResults.ml.margin, q.fullResults.amz.margin, q.fullResults.wal.margin);
      const platColor = {
        'ML': '#B45309',
        'AMZ': '#C2410C',
        'WAL': '#1D4ED8'
      };
      const platBg = {
        'ML': '#FEF9C3',
        'AMZ': '#FFF7ED',
        'WAL': '#EFF6FF'
      };
      const mlR = q.fullResults.ml,
        amzR = q.fullResults.amz,
        walR = q.fullResults.wal;
      const platRows = [{
        n: 'Mercado Libre',
        r: mlR,
        col: '#92400E',
        bg: '#FFFBEB'
      }, {
        n: 'Amazon',
        r: amzR,
        col: '#C2410C',
        bg: '#FFF7ED'
      }, {
        n: 'Walmart',
        r: walR,
        col: '#1D4ED8',
        bg: '#EFF6FF'
      }];
      return `
      <div class="prod-card" style="margin-bottom:18px;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden;break-inside:avoid;">
        <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:#F9FAFB;border-bottom:1px solid #E5E7EB;">
          <div style="display:flex;align-items:center;gap:10px;">
            <span style="width:22px;height:22px;border-radius:50%;background:#065F46;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;">${i + 1}</span>
            <div>
              <div style="font-size:13px;font-weight:700;color:#111827;">${q.name}</div>
              <div style="font-size:11px;color:#6B7280;margin-top:1px;">${q.category}${q.supplier ? ' · Proveedor: ' + q.supplier : ''}</div>
            </div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:10px;color:#6B7280;text-transform:uppercase;letter-spacing:.05em;">Costo producto</div>
            <div style="font-size:13px;font-weight:700;color:#111827;font-family:monospace;">${fmt(q.costMXN)}</div>
          </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0;">
          ${platRows.map((p, pi) => `
          <div style="padding:10px 14px;${pi < 2 ? 'border-right:1px solid #E5E7EB;' : ''}">
            <div style="font-size:10px;font-weight:700;color:${p.col};text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">${p.n}</div>
            <div style="font-size:10px;color:#6B7280;margin-bottom:1px;">Precio: <span style="color:#111827;font-family:monospace;">${fmt(p.r.price)}</span></div>
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:4px;">
              <span style="font-size:10px;color:#6B7280;">Margen neto</span>
              <span style="font-size:14px;font-weight:800;font-family:monospace;color:${p.r.margin < 0 ? '#DC2626' : p.r.margin === bM ? '#065F46' : '#374151'};">${p.r.margin.toFixed(2)}%</span>
            </div>
            <div style="height:3px;background:#E5E7EB;border-radius:99px;margin-bottom:6px;overflow:hidden;">
              <div style="height:100%;width:${Math.min(Math.max(p.r.margin, 0), 100)}%;background:${p.r.margin < 0 ? '#DC2626' : p.r.margin === bM ? '#059669' : '#9CA3AF'};border-radius:99px;"></div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;">
              <div style="background:${p.col + '11'};border-radius:4px;padding:4px 6px;">
                <div style="font-size:9px;color:#6B7280;">Utilidad</div>
                <div style="font-size:11px;font-weight:700;font-family:monospace;color:${p.r.profit < 0 ? '#DC2626' : '#065F46'};">${fmt(p.r.profit)}</div>
              </div>
              <div style="background:#F3F4F6;border-radius:4px;padding:4px 6px;">
                <div style="font-size:9px;color:#6B7280;">ROI</div>
                <div style="font-size:11px;font-weight:700;font-family:monospace;color:${p.r.roi < 0 ? '#DC2626' : '#374151'};">${p.r.roi.toFixed(1)}%</div>
              </div>
            </div>
            ${p.r.discAmt > 0 ? `<div style="font-size:9px;color:#059669;margin-top:4px;">+ Desc. ${fmt(p.r.discAmt)}</div>` : ''}
            ${p.r.msiAmt > 0 ? `<div style="font-size:9px;color:#DC2626;margin-top:2px;">− MSI ${fmt(p.r.msiAmt)}</div>` : ''}
          </div>`).join('')}
        </div>
        <div style="padding:8px 14px;background:#F9FAFB;border-top:1px solid #E5E7EB;display:flex;align-items:center;justify-content:space-between;">
          <div style="font-size:10px;color:#6B7280;">Mejor plataforma: <span style="font-weight:700;color:#111827;">${{
        ML: 'Mercado Libre',
        AMZ: 'Amazon',
        WAL: 'Walmart'
      }[q.bestPlatform] || q.bestPlatform}</span></div>
          <div style="font-size:10px;color:#6B7280;">Mejor utilidad: <span style="font-weight:700;font-family:monospace;color:#065F46;">${fmt(bP)}</span> · Margen: <span style="font-weight:700;font-family:monospace;color:#065F46;">${bM.toFixed(2)}%</span></div>
        </div>
      </div>`;
    }).join('');
    const html = `<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Reporte SmartScouting — ${date}</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0;}
  body{font-family:'Inter',Arial,sans-serif;background:#fff;color:#111827;padding:32px;font-size:12px;}
  @page{size:A4;margin:1.5cm 1.2cm;}
  @media print{body{padding:0;}.no-print{display:none!important;}}
  .header{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:24px;padding-bottom:16px;border-bottom:2px solid #065F46;}
  .logo{display:flex;align-items:center;gap:8px;}
  .logo-dot{width:10px;height:10px;border-radius:50%;background:#065F46;flex-shrink:0;}
  .summary-grid{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;margin-bottom:20px;}
  .sum-card{background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:10px 12px;}
  .sum-label{font-size:9px;text-transform:uppercase;letter-spacing:.06em;color:#6B7280;margin-bottom:3px;}
  .sum-val{font-size:20px;font-weight:800;font-family:monospace;color:#111827;}
  .sum-sub{font-size:10px;color:#6B7280;margin-top:1px;}
  .section-title{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em;color:#6B7280;margin:0 0 12px;padding-bottom:6px;border-bottom:1px solid #E5E7EB;}
  .prod-card{break-inside:avoid;}
</style>
</head>
<body>
<div class="header">
  <div class="logo">
    <div class="logo-dot"></div>
    <div>
      <div style="font-size:20px;font-weight:900;letter-spacing:-.02em;color:#111827;">SmartScouting</div>
      <div style="font-size:11px;color:#6B7280;margin-top:2px;">Reporte de cotizaciones · ${date}</div>
    </div>
  </div>
  <div style="text-align:right;">
    <div style="font-size:11px;color:#6B7280;">Generado el ${date}</div>
    <div style="font-size:11px;color:#6B7280;margin-top:2px;">${selQuotes.length} cotizaciones seleccionadas</div>
  </div>
</div>
<div class="summary-grid">
  <div class="sum-card"><div class="sum-label">Cotizaciones</div><div class="sum-val" style="color:#065F46;">${selQuotes.length}</div><div class="sum-sub">${rentCount} rentables</div></div>
  <div class="sum-card"><div class="sum-label">Margen prom. (mejor)</div><div class="sum-val">${avgBestMargin.toFixed(1)}%</div><div class="sum-sub">Promedio de mejor canal</div></div>
  <div class="sum-card"><div class="sum-label">Utilidad total proyectada</div><div class="sum-val" style="color:#065F46;font-size:15px;">${fmt(totalBestProfit)}</div><div class="sum-sub">Suma mejor canal por producto</div></div>
  <div class="sum-card"><div class="sum-label">Costo total</div><div class="sum-val" style="font-size:15px;">${fmt(selQuotes.reduce((s, q) => s + q.costMXN, 0))}</div><div class="sum-sub">Suma costos en MXN</div></div>
</div>
<div class="section-title">Detalle por cotización</div>
${rows}
<div style="margin-top:24px;padding-top:12px;border-top:1px solid #E5E7EB;display:flex;justify-content:space-between;font-size:10px;color:#9CA3AF;">
  <span>SmartScouting · Simulador de Márgenes para Marketplaces MX</span>
  <span>Reporte generado el ${date}</span>
</div>
</body></html>`;
    const w = window.open('', '_blank', 'width=900,height=700');
    w.document.write(html);
    w.document.close();
    w.onload = () => {
      w.print();
    };
  };
  const clearAll = () => {
    setSearch('');
    setCatF('all');
    setPlatF('all');
    setProvF('all');
    setProfF('all');
  };
  const nAvanzados = (catF !== 'all' ? 1 : 0) + (platF !== 'all' ? 1 : 0) + (provF !== 'all' ? 1 : 0);
  const activeChips = [];
  if (search) activeChips.push({
    l: 'Búsqueda: "' + search + '"',
    c: () => setSearch('')
  });
  if (catF !== 'all') activeChips.push({
    l: 'Categoría: ' + catF,
    c: () => setCatF('all')
  });
  if (platF !== 'all') activeChips.push({
    l: 'Canal: ' + ({
      ML: 'Mercado Libre',
      AMZ: 'Amazon',
      WAL: 'Walmart'
    }[platF] || platF),
    c: () => setPlatF('all')
  });
  if (provF !== 'all') activeChips.push({
    l: 'Proveedor: ' + provF,
    c: () => setProvF('all')
  });
  if (profF !== 'all') activeChips.push({
    l: 'Resultado: ' + (profF === 'positivo' ? 'Rentables' : 'Con pérdida'),
    c: () => setProfF('all')
  });
  const TH = ({
    k,
    children,
    align
  }) => /*#__PURE__*/React.createElement("th", {
    className: 'sortable' + (sortKey === k ? ' on' : ''),
    onClick: () => toggleSort(k),
    style: {
      textAlign: align || 'left'
    },
    title: "Clic para ordenar"
  }, /*#__PURE__*/React.createElement("span", {
    className: "th-in"
  }, children, /*#__PURE__*/React.createElement("span", {
    className: "th-ar"
  }, sortKey === k && sortDir === 'asc' ? /*#__PURE__*/React.createElement(SortAsc, {
    size: 11
  }) : /*#__PURE__*/React.createElement(SortDesc, {
    size: 11
  }))));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '0 24px 80px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "toolbar"
  }, /*#__PURE__*/React.createElement("div", {
    className: "tb-sec"
  }, /*#__PURE__*/React.createElement("div", {
    className: "tb-sec-hd"
  }, /*#__PURE__*/React.createElement(SlidersHorizontal, {
    size: 11
  }), "Filtrar"), /*#__PURE__*/React.createElement("div", {
    className: "tb-row"
  }, /*#__PURE__*/React.createElement("div", {
    className: "fw",
    style: {
      height: 34,
      flex: '1 1 260px'
    }
  }, /*#__PURE__*/React.createElement(Search, {
    size: 13,
    style: {
      flexShrink: 0,
      color: 'var(--t3)',
      marginLeft: 10
    }
  }), /*#__PURE__*/React.createElement("input", {
    type: "text",
    placeholder: "Buscar producto, categoría o proveedor…",
    value: search,
    onChange: e => setSearch(e.target.value),
    style: {
      height: 34,
      fontFamily: 'var(--sans)'
    }
  }), search && /*#__PURE__*/React.createElement("button", {
    onClick: () => setSearch(''),
    style: {
      background: 'none',
      border: 'none',
      cursor: 'pointer',
      color: 'var(--t3)',
      padding: '0 8px',
      display: 'flex'
    }
  }, /*#__PURE__*/React.createElement(X, {
    size: 12
  }))), /*#__PURE__*/React.createElement("div", {
    className: "seg-sm"
  }, [['all', 'Todos'], ['positivo', 'Rentables'], ['negativo', 'Con pérdida']].map(([v, l]) => /*#__PURE__*/React.createElement("button", {
    key: v,
    className: profF === v ? 'on' : '',
    onClick: () => setProfF(v)
  }, l))), /*#__PURE__*/React.createElement("button", {
    className: 'more-btn' + (showMore || nAvanzados > 0 ? ' on' : ''),
    onClick: () => setShowMore(m => !m)
  }, /*#__PURE__*/React.createElement(Filter, {
    size: 12
  }), "Más filtros", nAvanzados > 0 && /*#__PURE__*/React.createElement("span", {
    className: "cnt"
  }, nAvanzados), showMore ? /*#__PURE__*/React.createElement(ChevronDown, {
    size: 13
  }) : /*#__PURE__*/React.createElement(ChevronRight, {
    size: 13
  }))), showMore && /*#__PURE__*/React.createElement("div", {
    className: "tb-row",
    style: {
      marginTop: 12,
      paddingTop: 12,
      borderTop: '0.5px solid var(--border)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "tb-field"
  }, /*#__PURE__*/React.createElement("label", null, "Categoría"), /*#__PURE__*/React.createElement("select", {
    className: "sel",
    style: {
      height: 34,
      width: 170,
      fontSize: 11
    },
    value: catF,
    onChange: e => setCatF(e.target.value)
  }, /*#__PURE__*/React.createElement("option", {
    value: "all"
  }, "Todas"), cats.filter(c => c !== 'all').map(c => /*#__PURE__*/React.createElement("option", {
    key: c,
    value: c
  }, c)))), /*#__PURE__*/React.createElement("div", {
    className: "tb-field"
  }, /*#__PURE__*/React.createElement("label", null, "Mejor canal"), /*#__PURE__*/React.createElement("select", {
    className: "sel",
    style: {
      height: 34,
      width: 160,
      fontSize: 11
    },
    value: platF,
    onChange: e => setPlatF(e.target.value)
  }, /*#__PURE__*/React.createElement("option", {
    value: "all"
  }, "Todos"), /*#__PURE__*/React.createElement("option", {
    value: "ML"
  }, "Mercado Libre"), /*#__PURE__*/React.createElement("option", {
    value: "AMZ"
  }, "Amazon"), /*#__PURE__*/React.createElement("option", {
    value: "WAL"
  }, "Walmart"))), provs.length > 1 && /*#__PURE__*/React.createElement("div", {
    className: "tb-field"
  }, /*#__PURE__*/React.createElement("label", null, "Proveedor"), /*#__PURE__*/React.createElement("select", {
    className: "sel",
    style: {
      height: 34,
      width: 170,
      fontSize: 11
    },
    value: provF,
    onChange: e => setProvF(e.target.value)
  }, /*#__PURE__*/React.createElement("option", {
    value: "all"
  }, "Todos"), provs.filter(p => p !== 'all').map(p => /*#__PURE__*/React.createElement("option", {
    key: p,
    value: p
  }, p)))))), /*#__PURE__*/React.createElement("div", {
    className: "tb-sec"
  }, /*#__PURE__*/React.createElement("div", {
    className: "tb-sec-hd"
  }, /*#__PURE__*/React.createElement(Tags, {
    size: 11
  }), "Agrupar resultados"), /*#__PURE__*/React.createElement("div", {
    className: "tb-row"
  }, [['none', 'Sin agrupar'], ['month', 'Por mes'], ['category', 'Por categoría'], ['platform', 'Por plataforma'], ['supplier', 'Por proveedor']].map(([v, l]) => /*#__PURE__*/React.createElement("button", {
    key: v,
    className: 'filter-chip' + (groupBy === v ? ' active' : ''),
    onClick: () => setGroupBy(v)
  }, l)), groupBy !== 'none' && /*#__PURE__*/React.createElement("div", {
    style: {
      marginLeft: 'auto',
      display: 'flex',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    style: {
      height: 26,
      padding: '0 10px',
      fontSize: 10
    },
    onClick: () => {
      const n = {};
      grouped.forEach(g => n[g.key] = true);
      setExpanded(n);
    }
  }, /*#__PURE__*/React.createElement(ChevronDown, {
    size: 11
  }), "Abrir todo"), /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    style: {
      height: 26,
      padding: '0 10px',
      fontSize: 10
    },
    onClick: () => {
      const n = {};
      grouped.forEach(g => n[g.key] = false);
      setExpanded(n);
    }
  }, /*#__PURE__*/React.createElement(ChevronRight, {
    size: 11
  }), "Cerrar todo")))), /*#__PURE__*/React.createElement("div", {
    className: "chips-row"
  }, /*#__PURE__*/React.createElement("span", {
    className: "res-count"
  }, /*#__PURE__*/React.createElement("strong", null, filtered.length), " de ", quotes.length, " cotizaciones"), activeChips.length > 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      width: '0.5px',
      height: 14,
      background: 'var(--border-s)'
    }
  }), activeChips.map((c, i) => /*#__PURE__*/React.createElement("span", {
    key: i,
    className: "chip-act"
  }, c.l, /*#__PURE__*/React.createElement("button", {
    onClick: c.c,
    title: "Quitar filtro"
  }, /*#__PURE__*/React.createElement(X, {
    size: 11
  })))), hasFilters ? /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    style: {
      height: 26,
      padding: '0 10px',
      fontSize: 10,
      marginLeft: 'auto'
    },
    onClick: clearAll
  }, /*#__PURE__*/React.createElement(RefreshCw, {
    size: 11
  }), "Limpiar todo") : /*#__PURE__*/React.createElement("span", {
    style: {
      marginLeft: 'auto',
      fontSize: 10,
      color: 'var(--t4)'
    }
  }, "Ordena haciendo clic en los encabezados de la tabla"))), filtered.length === 0 ? /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'center',
      padding: '40px 0',
      color: 'var(--t3)',
      fontSize: 13
    }
  }, "Sin resultados con los filtros actuales.") : /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement("table", {
    className: "tbl"
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: {
      width: 40,
      textAlign: 'center'
    }
  }, /*#__PURE__*/React.createElement("button", {
    style: {
      background: 'none',
      border: 'none',
      cursor: 'pointer',
      display: 'flex',
      margin: '0 auto'
    },
    onClick: toggleAll
  }, allSel ? /*#__PURE__*/React.createElement(CheckSquare, {
    size: 14,
    color: "var(--accent)"
  }) : /*#__PURE__*/React.createElement(Square, {
    size: 14
  }))), /*#__PURE__*/React.createElement(TH, {
    k: "date"
  }, "Canal"), /*#__PURE__*/React.createElement(TH, {
    k: "name"
  }, "Producto"), /*#__PURE__*/React.createElement(TH, {
    k: "supplier"
  }, "Proveedor"), /*#__PURE__*/React.createElement("th", null, "Cat."), /*#__PURE__*/React.createElement(TH, {
    k: "cost",
    align: "right"
  }, "Costo MXN"), /*#__PURE__*/React.createElement("th", {
    className: 'sortable' + (sortKey === 'margin' ? ' on' : ''),
    onClick: () => toggleSort('margin'),
    style: {
      textAlign: 'center',
      background: 'rgba(250,204,21,.04)'
    },
    title: "Ordenar por mejor margen"
  }, /*#__PURE__*/React.createElement("span", {
    className: "th-in"
  }, "ML", /*#__PURE__*/React.createElement("span", {
    className: "th-ar"
  }, sortKey === 'margin' && sortDir === 'asc' ? /*#__PURE__*/React.createElement(SortAsc, {
    size: 11
  }) : /*#__PURE__*/React.createElement(SortDesc, {
    size: 11
  })))), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: 'center',
      background: 'rgba(249,115,22,.04)'
    }
  }, "Amazon"), /*#__PURE__*/React.createElement("th", {
    className: 'sortable' + (sortKey === 'profit' ? ' on' : ''),
    onClick: () => toggleSort('profit'),
    style: {
      textAlign: 'center',
      background: 'rgba(59,130,246,.04)'
    },
    title: "Ordenar por mejor utilidad"
  }, /*#__PURE__*/React.createElement("span", {
    className: "th-in"
  }, "Walmart", /*#__PURE__*/React.createElement("span", {
    className: "th-ar"
  }, sortKey === 'profit' && sortDir === 'asc' ? /*#__PURE__*/React.createElement(SortAsc, {
    size: 11
  }) : /*#__PURE__*/React.createElement(SortDesc, {
    size: 11
  })))), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: 'center'
    }
  }, "Acción"))), /*#__PURE__*/React.createElement("tbody", null, grouped.map(grp => /*#__PURE__*/React.createElement(React.Fragment, {
    key: grp.key
  }, groupBy !== 'none' && /*#__PURE__*/React.createElement("tr", {
    style: {
      background: 'var(--s2)',
      cursor: 'pointer'
    },
    onClick: () => toggleGroup(grp.key)
  }, /*#__PURE__*/React.createElement("td", {
    colSpan: 10,
    style: {
      padding: '7px 16px',
      fontWeight: 700,
      fontSize: 10,
      textTransform: 'uppercase',
      letterSpacing: '.07em',
      color: 'var(--t3)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, expanded[grp.key] !== false ? /*#__PURE__*/React.createElement(ChevronDown, {
    size: 13
  }) : /*#__PURE__*/React.createElement(ChevronRight, {
    size: 13
  }), grp.key, " · ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--t2)'
    }
  }, grp.items.length, " producto", grp.items.length !== 1 ? 's' : '')))), (expanded[grp.key] !== false || groupBy === 'none') && grp.items.map(q => {
    const bP = Math.max(q.fullResults.ml.profit, q.fullResults.amz.profit, q.fullResults.wal.profit);
    return /*#__PURE__*/React.createElement("tr", {
      key: q.id,
      onDoubleClick: () => onLoad(q),
      style: {
        cursor: 'pointer'
      }
    }, /*#__PURE__*/React.createElement("td", {
      style: {
        textAlign: 'center'
      }
    }, /*#__PURE__*/React.createElement("button", {
      style: {
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        display: 'flex',
        margin: '0 auto'
      },
      onClick: e => {
        e.stopPropagation();
        const n = new Set(selected);
        n.has(q.id) ? n.delete(q.id) : n.add(q.id);
        setSelected(n);
      }
    }, selected.has(q.id) ? /*#__PURE__*/React.createElement(CheckSquare, {
      size: 14,
      color: "var(--accent)"
    }) : /*#__PURE__*/React.createElement(Square, {
      size: 14,
      color: "var(--t4)"
    }))), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10,
        fontWeight: 700,
        padding: '2px 7px',
        borderRadius: 4,
        background: q.bestPlatform === 'ML' ? 'rgba(250,204,21,.15)' : q.bestPlatform === 'AMZ' ? 'rgba(249,115,22,.15)' : 'rgba(59,130,246,.15)',
        color: q.bestPlatform === 'ML' ? '#FACC15' : q.bestPlatform === 'AMZ' ? '#F97316' : '#3B82F6'
      }
    }, q.bestPlatform)), /*#__PURE__*/React.createElement("td", {
      style: {
        maxWidth: 180
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontWeight: 600,
        fontSize: 12,
        color: 'var(--t1)',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis'
      }
    }, q.name), ES_ADMIN() && q.autor ? /*#__PURE__*/React.createElement("div", {
      style: { fontSize: 9.5, color: 'var(--t4)', marginTop: 2 }
    }, q.autor) : null), /*#__PURE__*/React.createElement("td", null, q.supplier ? /*#__PURE__*/React.createElement("span", {
      className: "prov-tag"
    }, /*#__PURE__*/React.createElement(Building2, {
      size: 10
    }), q.supplier) : /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10,
        color: 'var(--t4)'
      }
    }, "—")), /*#__PURE__*/React.createElement("td", null, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 10,
        color: 'var(--t3)'
      }
    }, q.category)), /*#__PURE__*/React.createElement("td", {
      style: {
        textAlign: 'right',
        fontFamily: 'var(--mono)',
        fontSize: 11
      }
    }, fmt(q.costMXN)), ['ml', 'amz', 'wal'].map(k => {
      const r = q.fullResults[k];
      return /*#__PURE__*/React.createElement("td", {
        key: k,
        style: {
          textAlign: 'center'
        }
      }, /*#__PURE__*/React.createElement("div", {
        style: {
          fontSize: 10,
          color: 'var(--t3)',
          marginBottom: 1
        }
      }, fmt(r.price)), /*#__PURE__*/React.createElement("div", {
        style: {
          fontWeight: 700,
          fontFamily: 'var(--mono)',
          fontSize: 12,
          color: r.profit < 0 ? 'var(--danger)' : eq(r.profit, bP) && bP > 0 ? 'var(--accent)' : 'var(--t2)'
        }
      }, fmtPct(r.margin)), /*#__PURE__*/React.createElement("div", {
        style: {
          fontSize: 10,
          fontFamily: 'var(--mono)',
          color: r.profit < 0 ? 'var(--danger)' : 'var(--t3)'
        }
      }, fmt(r.profit)));
    }), /*#__PURE__*/React.createElement("td", {
      style: {
        textAlign: 'center'
      }
    }, /*#__PURE__*/React.createElement("button", {
      className: "btn bg",
      style: {
        height: 26,
        padding: '0 10px',
        fontSize: 10
      },
      onClick: e => {
        e.stopPropagation();
        onLoad(q);
      }
    }, /*#__PURE__*/React.createElement(Edit3, {
      size: 11
    }), "Cargar")));
  })))))), selected.size > 0 && /*#__PURE__*/React.createElement("div", {
    className: "sel-bar"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 6
    }
  }, /*#__PURE__*/React.createElement(CheckSquare, {
    size: 15,
    color: "var(--accent)"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 700,
      color: 'var(--t1)'
    }
  }, selected.size, " seleccionado", selected.size !== 1 ? 's' : '')), /*#__PURE__*/React.createElement("div", {
    style: {
      width: '0.5px',
      height: 18,
      background: 'var(--border-s)'
    }
  }), /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    style: {
      height: 30,
      fontSize: 11
    },
    onClick: () => {
      const n = new Set(selected);
      filtered.forEach(q => n.add(q.id));
      setSelected(n);
    }
  }, "Seleccionar página"), /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    style: {
      height: 30,
      fontSize: 11,
      background: 'var(--pr-dim)',
      color: '#A78BFA',
      border: '0.5px solid var(--pr-b)'
    },
    onClick: exportPDF
  }, /*#__PURE__*/React.createElement(Download, {
    size: 12
  }), "Exportar PDF (", selected.size, ")"), /*#__PURE__*/React.createElement("button", {
    className: "btn bd",
    style: {
      height: 30,
      fontSize: 11
    },
    onClick: () => {
      onDelete(selected);
      setSelected(new Set());
    }
  }, /*#__PURE__*/React.createElement(Trash2, {
    size: 12
  }), "Eliminar ", selected.size), /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    style: {
      height: 30,
      fontSize: 11
    },
    onClick: () => setSelected(new Set())
  }, /*#__PURE__*/React.createElement(X, {
    size: 12
  }), "Limpiar")));
}

/* ─── SETTINGS ──────────────────────────────────────────────────────────────── */
function SettingsModal({
  show,
  onClose,
  exchangeRate,
  setExchangeRate,
  mlGlobal,
  setMlGlobal,
  amzGlobal,
  setAmzGlobal,
  walGlobal,
  setWalGlobal,
  mlCfgs,
  setMlCfgs,
  amzCfgs,
  setAmzCfgs,
  walCfgs,
  setWalCfgs,
  onSave,
  tcStatus,
  tcRate,
  tcUpdated,
  tcSource,
  fetchTC
}) {
  const [tab, setTab] = useState('general');
  const [newCat, setNewCat] = useState('');
  const [q, setQ] = useState('');
  const [importMsg, setImportMsg] = useState('');
  const soloLectura = !ES_ADMIN();
  if (!show) return null;
  const addCat = () => {
    if (!newCat.trim()) return;
    const c = newCat.toUpperCase().trim();
    setMlCfgs(p => ({
      ...p,
      [c]: {
        clasica: 10,
        premium: 15,
        ship: 85
      }
    }));
    setAmzCfgs(p => ({
      ...p,
      [c]: {
        com: 10,
        ship: 85
      }
    }));
    setWalCfgs(p => ({
      ...p,
      [c]: {
        com: 14.5,
        ship: 63
      }
    }));
    setNewCat('');
  };
  const downloadCommTemplate = async () => {
    const XLSX = await loadXLSX();
    const mlRows = Object.entries(mlCfgs).map(([cat, v]) => [cat, v.clasica, v.premium, v.ship]);
    const amzRows = Object.entries(amzCfgs).map(([cat, v]) => [cat, v.com, v.ship]);
    const walRows = Object.entries(walCfgs).map(([cat, v]) => [cat, v.com, v.ship]);
    const wb = XLSX.utils.book_new();
    const wsML = XLSX.utils.aoa_to_sheet([['CATEGORIA', 'CLASICA_%', 'PREMIUM_%', 'ENVIO_MXN'], ...mlRows]);
    const wsAMZ = XLSX.utils.aoa_to_sheet([['CATEGORIA', 'COMISION_%', 'ENVIO_MXN'], ...amzRows]);
    const wsWAL = XLSX.utils.aoa_to_sheet([['CATEGORIA', 'COMISION_%', 'ENVIO_MXN'], ...walRows]);
    const wsG = XLSX.utils.aoa_to_sheet([['PLATAFORMA', 'PARAMETRO', 'VALOR'], ['ML', 'DESCUENTO_%', mlGlobal.discount], ['ML', 'RETENCION_%', mlGlobal.tax], ['ML', 'FACTOR_REFI', mlGlobal.factor], ['AMZ', 'DESCUENTO_%', amzGlobal.discount], ['AMZ', 'MSI_%', amzGlobal.msi], ['AMZ', 'RETENCION_%', amzGlobal.tax], ['AMZ', 'FACTOR_REFI', amzGlobal.factor], ['WAL', 'DESCUENTO_%', walGlobal.discount], ['WAL', 'RETENCION_%', walGlobal.tax], ['WAL', 'FACTOR_REFI', walGlobal.factor]]);
    wsML['!cols'] = [{
      wch: 25
    }, {
      wch: 12
    }, {
      wch: 12
    }, {
      wch: 12
    }];
    wsAMZ['!cols'] = [{
      wch: 25
    }, {
      wch: 12
    }, {
      wch: 12
    }];
    wsWAL['!cols'] = [{
      wch: 25
    }, {
      wch: 12
    }, {
      wch: 12
    }];
    wsG['!cols'] = [{
      wch: 12
    }, {
      wch: 16
    }, {
      wch: 10
    }];
    XLSX.utils.book_append_sheet(wb, wsML, 'Mercado_Libre');
    XLSX.utils.book_append_sheet(wb, wsAMZ, 'Amazon');
    XLSX.utils.book_append_sheet(wb, wsWAL, 'Walmart');
    XLSX.utils.book_append_sheet(wb, wsG, 'Globales');
    XLSX.writeFile(wb, 'Comisiones_SmartScouting.xlsx');
  };
  const importCommFile = async ev => {
    const file = ev.target.files[0];
    if (!file) return;
    setImportMsg('Procesando...');
    const XLSX = await loadXLSX();
    const reader = new FileReader();
    reader.onload = e => {
      try {
        const wb = XLSX.read(new Uint8Array(e.target.result), {
          type: 'array'
        });
        let ok = 0;
        const wsML = wb.Sheets['Mercado_Libre'] || wb.Sheets[wb.SheetNames[0]];
        if (wsML) {
          const rows = XLSX.utils.sheet_to_json(wsML, {
            header: 1
          }).slice(1);
          const n = {};
          rows.forEach(r => {
            if (r[0]) n[r[0].toString().toUpperCase().trim()] = {
              clasica: cn(r[1]),
              premium: cn(r[2]),
              ship: cn(r[3])
            };
          });
          if (Object.keys(n).length > 0) {
            setMlCfgs(p => ({
              ...p,
              ...n
            }));
            ok++;
          }
        }
        const wsAMZ = wb.Sheets['Amazon'] || (wb.SheetNames[1] ? wb.Sheets[wb.SheetNames[1]] : null);
        if (wsAMZ) {
          const rows = XLSX.utils.sheet_to_json(wsAMZ, {
            header: 1
          }).slice(1);
          const n = {};
          rows.forEach(r => {
            if (r[0]) n[r[0].toString().toUpperCase().trim()] = {
              com: cn(r[1]),
              ship: cn(r[2])
            };
          });
          if (Object.keys(n).length > 0) {
            setAmzCfgs(p => ({
              ...p,
              ...n
            }));
            ok++;
          }
        }
        const wsWAL = wb.Sheets['Walmart'] || (wb.SheetNames[2] ? wb.Sheets[wb.SheetNames[2]] : null);
        if (wsWAL) {
          const rows = XLSX.utils.sheet_to_json(wsWAL, {
            header: 1
          }).slice(1);
          const n = {};
          rows.forEach(r => {
            if (r[0]) n[r[0].toString().toUpperCase().trim()] = {
              com: cn(r[1]),
              ship: cn(r[2])
            };
          });
          if (Object.keys(n).length > 0) {
            setWalCfgs(p => ({
              ...p,
              ...n
            }));
            ok++;
          }
        }
        const wsG = wb.Sheets['Globales'] || (wb.SheetNames[3] ? wb.Sheets[wb.SheetNames[3]] : null);
        if (wsG) {
          const rows = XLSX.utils.sheet_to_json(wsG, {
            header: 1
          }).slice(1);
          rows.forEach(r => {
            const pl = (r[0] || '').toString().toUpperCase();
            const pa = (r[1] || '').toString().toUpperCase();
            const v = cn(r[2]);
            if (pl === 'ML') {
              if (pa === 'DESCUENTO_%') setMlGlobal(p => ({
                ...p,
                discount: v
              }));
              if (pa === 'RETENCION_%') setMlGlobal(p => ({
                ...p,
                tax: v
              }));
              if (pa === 'FACTOR_REFI') setMlGlobal(p => ({
                ...p,
                factor: v
              }));
            }
            if (pl === 'AMZ') {
              if (pa === 'DESCUENTO_%') setAmzGlobal(p => ({
                ...p,
                discount: v
              }));
              if (pa === 'MSI_%') setAmzGlobal(p => ({
                ...p,
                msi: v
              }));
              if (pa === 'RETENCION_%') setAmzGlobal(p => ({
                ...p,
                tax: v
              }));
              if (pa === 'FACTOR_REFI') setAmzGlobal(p => ({
                ...p,
                factor: v
              }));
            }
            if (pl === 'WAL') {
              if (pa === 'DESCUENTO_%') setWalGlobal(p => ({
                ...p,
                discount: v
              }));
              if (pa === 'RETENCION_%') setWalGlobal(p => ({
                ...p,
                tax: v
              }));
              if (pa === 'FACTOR_REFI') setWalGlobal(p => ({
                ...p,
                factor: v
              }));
            }
          });
        }
        setImportMsg(ok > 0 ? `✓ ${ok} hoja${ok !== 1 ? 's' : ''} importada${ok !== 1 ? 's' : ''} correctamente` : '⚠ No se encontraron hojas reconocibles');
        setTimeout(() => setImportMsg(''), 4000);
      } catch (err) {
        setImportMsg('✗ Error al leer el archivo');
        setTimeout(() => setImportMsg(''), 3000);
      }
    };
    reader.readAsArrayBuffer(file);
    ev.target.value = '';
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "mo",
    onClick: e => e.target === e.currentTarget && onClose()
  }, /*#__PURE__*/React.createElement("div", {
    className: soloLectura ? "md solo-lectura" : "md",
    style: {
      maxWidth: 940
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "mh"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Settings, {
    size: 16,
    color: "var(--accent)"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      fontWeight: 700
    }
  }, soloLectura ? "Configuración (solo lectura)" : "Configuración")), /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    style: {
      background: 'none',
      border: 'none',
      cursor: 'pointer',
      color: 'var(--t3)',
      display: 'flex'
    }
  }, /*#__PURE__*/React.createElement(X, {
    size: 18
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '12px 20px 0',
      flexShrink: 0,
      borderBottom: '0.5px solid var(--border)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "tb",
    style: {
      width: 'fit-content'
    }
  }, [['general', '⚙ General'], ['comisiones', '📊 Comisiones'], ['ml', 'ML'], ['amz', 'Amazon'], ['wal', 'Walmart']].map(([k, l]) => /*#__PURE__*/React.createElement("button", {
    key: k,
    className: 'tbb' + (tab === k ? ' on' : ''),
    onClick: () => setTab(k)
  }, l)))), /*#__PURE__*/React.createElement("div", {
    className: "mb"
  }, tab === 'general' && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 12,
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      padding: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "lbl",
    style: {
      justifyContent: 'center',
      marginBottom: 6
    }
  }, "Tipo de cambio USD → MXN"), /*#__PURE__*/React.createElement("input", {
    type: "number",
    step: "0.01",
    value: exchangeRate,
    onChange: e => setExchangeRate(cn(e.target.value)),
    style: {
      width: '100%',
      textAlign: 'center',
      fontSize: 36,
      fontWeight: 800,
      background: 'transparent',
      border: 'none',
      color: 'var(--accent)',
      outline: 'none',
      fontFamily: 'var(--mono)',
      marginBottom: 10
    }
  }), tcStatus === 'ok' && tcRate && /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--ac-dim)',
      border: '0.5px solid var(--ac-b)',
      borderRadius: 6,
      padding: '8px 12px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 8
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--accent)',
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: '.05em'
    }
  }, "En vivo · ", tcSource), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--t2)',
      marginTop: 2
    }
  }, "Act. ", tcUpdated)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 20,
      fontWeight: 800,
      fontFamily: 'var(--mono)',
      color: 'var(--accent)'
    }
  }, tcRate?.toFixed(2))), tcStatus === 'error' && /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--wn-dim)',
      border: '0.5px solid var(--wn-b)',
      borderRadius: 6,
      padding: '8px 12px',
      fontSize: 11,
      color: 'var(--warn)',
      marginBottom: 8
    }
  }, "Sin conexión — TC editable manualmente."), /*#__PURE__*/React.createElement("button", {
    className: "btn bg",
    style: {
      width: '100%',
      justifyContent: 'center',
      fontSize: 11
    },
    onClick: () => fetchTC(true)
  }, /*#__PURE__*/React.createElement(RefreshCw, {
    size: 12
  }), "Actualizar tipo de cambio")), /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      padding: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "lbl",
    style: {
      marginBottom: 10
    }
  }, "Agregar categoría nueva"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 8,
      marginBottom: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "fw",
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("input", {
    type: "text",
    value: newCat,
    onChange: e => setNewCat(e.target.value),
    onKeyDown: e => e.key === 'Enter' && addCat(),
    placeholder: "Ej. GAMING",
    style: {
      height: 36,
      padding: '0 10px',
      fontFamily: 'var(--sans)'
    }
  })), /*#__PURE__*/React.createElement("button", {
    className: "btn bp",
    onClick: addCat
  }, /*#__PURE__*/React.createElement(Plus, {
    size: 14
  }), "Añadir")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--t3)'
    }
  }, "Se agrega a ML, Amazon y Walmart con valores base editables."))), /*#__PURE__*/React.createElement("button", {
    className: "btn bp",
    style: {
      width: '100%',
      height: 40,
      justifyContent: 'center',
      fontSize: 12
    },
    onClick: () => {
      onSave();
      onClose();
    }
  }, /*#__PURE__*/React.createElement(Save, {
    size: 14
  }), "Guardar y cerrar")), tab === 'comisiones' && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--ac-dim)',
      border: '0.5px solid var(--ac-b)',
      borderRadius: 10,
      padding: '14px 16px',
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      fontWeight: 700,
      color: 'var(--accent)',
      marginBottom: 4
    }
  }, "Gestión masiva de comisiones"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--t2)',
      lineHeight: 1.6
    }
  }, "Descarga la plantilla Excel con todas las comisiones actuales, edita los valores y vuelve a cargarla. Los cambios se aplican a las 3 plataformas simultáneamente.")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 12,
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      padding: 16,
      display: 'flex',
      flexDirection: 'column',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: 2
    }
  }, /*#__PURE__*/React.createElement(Download, {
    size: 16,
    color: "var(--accent)"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 700,
      color: 'var(--t1)'
    }
  }, "Descargar plantilla")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--t3)',
      lineHeight: 1.5
    }
  }, "Genera un Excel con 4 hojas (ML, Amazon, Walmart y Globales) con tus valores actuales precompletados."), /*#__PURE__*/React.createElement("button", {
    className: "btn bp",
    style: {
      justifyContent: 'center',
      marginTop: 'auto'
    },
    onClick: downloadCommTemplate
  }, /*#__PURE__*/React.createElement(Download, {
    size: 14
  }), "Descargar Comisiones.xlsx")), /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      padding: 16,
      display: 'flex',
      flexDirection: 'column',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: 2
    }
  }, /*#__PURE__*/React.createElement(Upload, {
    size: 16,
    color: "#A78BFA"
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 700,
      color: 'var(--t1)'
    }
  }, "Cargar archivo editado")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: 'var(--t3)',
      lineHeight: 1.5
    }
  }, "Sube el archivo con tus cambios. Reconoce las hojas por nombre automáticamente."), importMsg && /*#__PURE__*/React.createElement("div", {
    style: {
      background: importMsg.startsWith('✓') ? 'var(--ac-dim)' : importMsg.startsWith('⚠') ? 'var(--wn-dim)' : 'var(--dn-dim)',
      border: `0.5px solid ${importMsg.startsWith('✓') ? 'var(--ac-b)' : importMsg.startsWith('⚠') ? 'var(--wn-b)' : 'var(--dn-b)'}`,
      borderRadius: 6,
      padding: '8px 12px',
      fontSize: 11,
      color: importMsg.startsWith('✓') ? 'var(--accent)' : importMsg.startsWith('⚠') ? 'var(--warn)' : 'var(--danger)'
    }
  }, importMsg), /*#__PURE__*/React.createElement("label", {
    className: "btn bg",
    style: {
      justifyContent: 'center',
      cursor: 'pointer',
      marginTop: 'auto',
      background: 'var(--pr-dim)',
      color: '#A78BFA',
      border: '0.5px solid var(--pr-b)'
    }
  }, /*#__PURE__*/React.createElement(Upload, {
    size: 14
  }), "Cargar Comisiones.xlsx", /*#__PURE__*/React.createElement("input", {
    type: "file",
    accept: ".xlsx,.xls",
    style: {
      display: 'none'
    },
    onChange: importCommFile
  })))), /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      padding: '12px 16px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "sec-ttl",
    style: {
      marginBottom: 10
    }
  }, "Estructura del archivo"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 8
    }
  }, [{
    hoja: 'Mercado_Libre',
    cols: 'CATEGORIA | CLASICA_% | PREMIUM_% | ENVIO_MXN'
  }, {
    hoja: 'Amazon',
    cols: 'CATEGORIA | COMISION_% | ENVIO_MXN'
  }, {
    hoja: 'Walmart',
    cols: 'CATEGORIA | COMISION_% | ENVIO_MXN'
  }, {
    hoja: 'Globales',
    cols: 'PLATAFORMA | PARAMETRO | VALOR'
  }].map(h => /*#__PURE__*/React.createElement("div", {
    key: h.hoja,
    style: {
      background: 'var(--s2)',
      borderRadius: 6,
      padding: '8px 12px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      color: 'var(--t1)',
      marginBottom: 3,
      fontFamily: 'var(--mono)'
    }
  }, h.hoja), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--t3)',
      fontFamily: 'var(--mono)'
    }
  }, h.cols)))))), tab === 'ml' && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr 1fr',
      gap: 10,
      marginBottom: 16
    }
  }, [['discount', 'Desc. Plataforma (%)'], ['tax', 'Retención ISR/IVA (%)'], ['factor', 'Factor REFI']].map(([k, l]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    className: "card",
    style: {
      padding: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "lbl",
    style: {
      marginBottom: 6
    }
  }, l), /*#__PURE__*/React.createElement("input", {
    type: "number",
    step: "0.01",
    className: "ism",
    value: mlGlobal[k] ?? '',
    onChange: e => setMlGlobal(p => ({
      ...p,
      [k]: cn(e.target.value)
    }))
  })))), /*#__PURE__*/React.createElement("div", {
    className: "fw",
    style: {
      marginBottom: 12,
      height: 34
    }
  }, /*#__PURE__*/React.createElement(Search, {
    size: 14,
    style: {
      flexShrink: 0,
      color: 'var(--t3)',
      marginLeft: 10
    }
  }), /*#__PURE__*/React.createElement("input", {
    type: "text",
    placeholder: "Buscar categoría...",
    value: q,
    onChange: e => setQ(e.target.value),
    style: {
      height: 34,
      fontFamily: 'var(--sans)'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '2fr 1fr 1fr 1fr',
      gap: 8,
      padding: '6px 12px',
      marginBottom: 4
    }
  }, ['Categoría', 'Clásica (%)', 'Premium (%)', 'Envío ($)'].map(h => /*#__PURE__*/React.createElement("div", {
    key: h,
    style: {
      fontSize: 10,
      fontWeight: 700,
      color: 'var(--t3)',
      textTransform: 'uppercase',
      letterSpacing: '.05em'
    }
  }, h))), Object.keys(mlCfgs).filter(c => c.includes(q.toUpperCase())).sort().map(cat => /*#__PURE__*/React.createElement("div", {
    key: cat,
    className: "cr",
    style: {
      gridTemplateColumns: '2fr 1fr 1fr 1fr'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      fontWeight: 600,
      color: 'var(--t2)',
      textTransform: 'uppercase'
    }
  }, cat), ['clasica', 'premium', 'ship'].map(k => /*#__PURE__*/React.createElement("input", {
    key: k,
    type: "number",
    className: "ism",
    value: mlCfgs[cat]?.[k] ?? '',
    onChange: e => setMlCfgs(p => ({
      ...p,
      [cat]: {
        ...p[cat],
        [k]: cn(e.target.value)
      }
    }))
  }))))), tab === 'amz' && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr 1fr 1fr',
      gap: 10,
      marginBottom: 16
    }
  }, [['discount', 'Desc. (%)'], ['msi', 'MSI (%)'], ['tax', 'Retención (%)'], ['factor', 'Factor REFI']].map(([k, l]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    className: "card",
    style: {
      padding: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "lbl",
    style: {
      marginBottom: 6
    }
  }, l), /*#__PURE__*/React.createElement("input", {
    type: "number",
    step: "0.01",
    className: "ism",
    value: amzGlobal[k] ?? '',
    onChange: e => setAmzGlobal(p => ({
      ...p,
      [k]: cn(e.target.value)
    }))
  })))), /*#__PURE__*/React.createElement("div", {
    className: "fw",
    style: {
      marginBottom: 12,
      height: 34
    }
  }, /*#__PURE__*/React.createElement(Search, {
    size: 14,
    style: {
      flexShrink: 0,
      color: 'var(--t3)',
      marginLeft: 10
    }
  }), /*#__PURE__*/React.createElement("input", {
    type: "text",
    placeholder: "Buscar categoría...",
    value: q,
    onChange: e => setQ(e.target.value),
    style: {
      height: 34,
      fontFamily: 'var(--sans)'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '2fr 1fr 1fr',
      gap: 8,
      padding: '6px 12px',
      marginBottom: 4
    }
  }, ['Categoría', 'Comisión (%)', 'Envío ($)'].map(h => /*#__PURE__*/React.createElement("div", {
    key: h,
    style: {
      fontSize: 10,
      fontWeight: 700,
      color: 'var(--t3)',
      textTransform: 'uppercase',
      letterSpacing: '.05em'
    }
  }, h))), Object.keys(amzCfgs).filter(c => c.includes(q.toUpperCase())).sort().map(cat => /*#__PURE__*/React.createElement("div", {
    key: cat,
    className: "cr",
    style: {
      gridTemplateColumns: '2fr 1fr 1fr'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      fontWeight: 600,
      color: 'var(--t2)',
      textTransform: 'uppercase'
    }
  }, cat), ['com', 'ship'].map(k => /*#__PURE__*/React.createElement("input", {
    key: k,
    type: "number",
    className: "ism",
    value: amzCfgs[cat]?.[k] ?? '',
    onChange: e => setAmzCfgs(p => ({
      ...p,
      [cat]: {
        ...p[cat],
        [k]: cn(e.target.value)
      }
    }))
  }))))), tab === 'wal' && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr 1fr',
      gap: 10,
      marginBottom: 16
    }
  }, [['discount', 'Desc. (%)'], ['tax', 'Retención (%)'], ['factor', 'Factor REFI']].map(([k, l]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    className: "card",
    style: {
      padding: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "lbl",
    style: {
      marginBottom: 6
    }
  }, l), /*#__PURE__*/React.createElement("input", {
    type: "number",
    step: "0.01",
    className: "ism",
    value: walGlobal[k] ?? '',
    onChange: e => setWalGlobal(p => ({
      ...p,
      [k]: cn(e.target.value)
    }))
  })))), /*#__PURE__*/React.createElement("div", {
    className: "fw",
    style: {
      marginBottom: 12,
      height: 34
    }
  }, /*#__PURE__*/React.createElement(Search, {
    size: 14,
    style: {
      flexShrink: 0,
      color: 'var(--t3)',
      marginLeft: 10
    }
  }), /*#__PURE__*/React.createElement("input", {
    type: "text",
    placeholder: "Buscar categoría...",
    value: q,
    onChange: e => setQ(e.target.value),
    style: {
      height: 34,
      fontFamily: 'var(--sans)'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '2fr 1fr 1fr',
      gap: 8,
      padding: '6px 12px',
      marginBottom: 4
    }
  }, ['Categoría', 'Comisión (%)', 'Envío ($)'].map(h => /*#__PURE__*/React.createElement("div", {
    key: h,
    style: {
      fontSize: 10,
      fontWeight: 700,
      color: 'var(--t3)',
      textTransform: 'uppercase',
      letterSpacing: '.05em'
    }
  }, h))), Object.keys(walCfgs).filter(c => c.includes(q.toUpperCase())).sort().map(cat => /*#__PURE__*/React.createElement("div", {
    key: cat,
    className: "cr",
    style: {
      gridTemplateColumns: '2fr 1fr 1fr'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      fontWeight: 600,
      color: 'var(--t2)',
      textTransform: 'uppercase'
    }
  }, cat), ['com', 'ship'].map(k => /*#__PURE__*/React.createElement("input", {
    key: k,
    type: "number",
    className: "ism",
    value: walCfgs[cat]?.[k] ?? '',
    onChange: e => setWalCfgs(p => ({
      ...p,
      [cat]: {
        ...p[cat],
        [k]: cn(e.target.value)
      }
    }))
  }))))))));
}

/* ─── APP ───────────────────────────────────────────────────────────────────── */
function App() {
  const perfil = PERFIL();
  const esAdmin = ES_ADMIN();
  const [view, setView] = useState('calc');
  const [loading, setLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [theme, setTheme] = useState(() => localStorage.getItem('ss_theme') || 'dark');
  const [exchangeRate, setExchangeRate] = useState(18);
  const [mlGlobal, setMlGlobal] = useState({
    discount: 2.0,
    tax: 9.05,
    factor: 0.975
  });
  const [amzGlobal, setAmzGlobal] = useState({
    discount: 0.0,
    msi: 3.0,
    tax: 9.1,
    factor: 0.975
  });
  const [walGlobal, setWalGlobal] = useState({
    discount: 10.0,
    tax: 9.1,
    factor: 0.975
  });
  const [mlCfgs, setMlCfgs] = useState({
    'LAPTOPS': {
      clasica: 10.0,
      premium: 14.5,
      ship: 95.0
    },
    'AUDIFONOS': {
      clasica: 10.0,
      premium: 14.5,
      ship: 65.5
    },
    'TABLETS': {
      clasica: 10.0,
      premium: 14.5,
      ship: 74.5
    },
    'BOCINAS': {
      clasica: 10.0,
      premium: 14.5,
      ship: 122.5
    },
    'CAMARAS': {
      clasica: 10.0,
      premium: 14.5,
      ship: 74.5
    },
    'WEARABLES': {
      clasica: 10.0,
      premium: 14.5,
      ship: 70.0
    },
    'CONSOLAS': {
      clasica: 10.5,
      premium: 15.0,
      ship: 139.5
    },
    'COCINA': {
      clasica: 15.0,
      premium: 19.5,
      ship: 161.5
    },
    'ILUMINACION': {
      clasica: 15.0,
      premium: 19.5,
      ship: 74.5
    },
    'INTERNET': {
      clasica: 15.0,
      premium: 19.5,
      ship: 122.5
    },
    'CELULARES': {
      clasica: 12.5,
      premium: 17.0,
      ship: 70.0
    },
    "TV'S": {
      clasica: 12.5,
      premium: 17.0,
      ship: 349.0
    },
    'CELULARES REFURBISHED': {
      clasica: 12.5,
      premium: 17.0,
      ship: 70.0
    },
    'ACCESORIOS': {
      clasica: 40.8,
      premium: 45.3,
      ship: 0.0
    },
    'HEALTH CARE': {
      clasica: 13.0,
      premium: 17.5,
      ship: 74.5
    },
    'HERRAMIENTAS': {
      clasica: 10.0,
      premium: 13.5,
      ship: 95.0
    },
    'PERFUMERIA': {
      clasica: 10.0,
      premium: 13.0,
      ship: 84.5
    },
    'PROCESADORES': {
      clasica: 10.0,
      premium: 13.5,
      ship: 74.5
    },
    'GENERAL': {
      clasica: 10.5,
      premium: 15.0,
      ship: 85.0
    }
  });
  const [amzCfgs, setAmzCfgs] = useState({
    'LAPTOPS': {
      com: 10.0,
      ship: 90.70
    },
    'AUDIFONOS': {
      com: 2.0,
      ship: 67.45
    },
    'TABLETS': {
      com: 10.0,
      ship: 77.69
    },
    'WEARABLES': {
      com: 10.0,
      ship: 67.45
    },
    'CONSOLAS': {
      com: 8.0,
      ship: 117.51
    },
    'COCINA': {
      com: 15.0,
      ship: 146.09
    },
    'BOCINAS': {
      com: 10.0,
      ship: 77.69
    },
    'CELULARES': {
      com: 10.0,
      ship: 66.04
    },
    'ACCESORIOS': {
      com: 15.0,
      ship: 67.45
    },
    'CAMARAS': {
      com: 10.0,
      ship: 70.88
    },
    'HEALTH CARE': {
      com: 15.0,
      ship: 109.85
    },
    'HERRAMIENTAS': {
      com: 12.0,
      ship: 96.83
    },
    "TV'S": {
      com: 10.0,
      ship: 117.51
    },
    'ILUMINACION': {
      com: 10.0,
      ship: 90.70
    },
    'CELULARES REFURBISHED': {
      com: 2.0,
      ship: 66.04
    },
    'INTERNET': {
      com: 10.0,
      ship: 121.34
    },
    'PROCESADORES': {
      com: 11.0,
      ship: 67.45
    },
    'PERFUMERIA': {
      com: 10.0,
      ship: 84.50
    },
    'GENERAL': {
      com: 10.0,
      ship: 85.0
    }
  });
  const [walCfgs, setWalCfgs] = useState({
    'LAPTOPS': {
      com: 14.5,
      ship: 91.0
    },
    'AUDIFONOS': {
      com: 19.5,
      ship: 63.0
    },
    'TABLETS': {
      com: 14.5,
      ship: 76.0
    },
    'WEARABLES': {
      com: 14.5,
      ship: 63.0
    },
    'CONSOLAS': {
      com: 14.5,
      ship: 91.0
    },
    'COCINA': {
      com: 19.5,
      ship: 63.0
    },
    'BOCINAS': {
      com: 14.5,
      ship: 63.0
    },
    'CELULARES': {
      com: 14.5,
      ship: 63.0
    },
    'ACCESORIOS': {
      com: 15.0,
      ship: 63.0
    },
    'CAMARAS': {
      com: 14.5,
      ship: 63.0
    },
    'HEALTH CARE': {
      com: 19.5,
      ship: 91.0
    },
    'HERRAMIENTAS': {
      com: 19.5,
      ship: 95.0
    },
    "TV'S": {
      com: 14.5,
      ship: 110.0
    },
    'ILUMINACION': {
      com: 19.5,
      ship: 63.0
    },
    'CELULARES REFURBISHED': {
      com: 14.5,
      ship: 63.0
    },
    'INTERNET': {
      com: 10.0,
      ship: 91.0
    },
    'PROCESADORES': {
      com: 19.5,
      ship: 63.0
    },
    'PERFUMERIA': {
      com: 14.5,
      ship: 63.0
    },
    'GENERAL': {
      com: 14.5,
      ship: 63.0
    }
  });
  const [simName, setSimName] = useState('');
  const [simCost, setSimCost] = useState('');
  const [simCostCur, setSimCostCur] = useState('MXN');
  const [simCat, setSimCat] = useState('GENERAL');
  const [simSupplier, setSimSupplier] = useState('');
  const [simMLType, setSimMLType] = useState('CLASICA');
  const [prices, setPrices] = useState({
    ml: 0,
    amz: 0,
    wal: 0
  });
  const [savedQuotes, setSavedQuotes] = useState(window.__cotizaciones || []);
  const [avisoDB, setAvisoDB] = useState('');
  useEffect(() => {
    let el = document.getElementById('aviso-db');
    if (!avisoDB) { if (el) el.remove(); return; }
    if (!el) { el = document.createElement('div'); el.id = 'aviso-db'; el.className = 'aviso-db'; document.body.appendChild(el); }
    el.textContent = avisoDB;
    const t = setTimeout(() => setAvisoDB(''), 8000);
    return () => clearTimeout(t);
  }, [avisoDB]);
  const [tcRate, setTcRate] = useState(null);
  const [tcStatus, setTcStatus] = useState('idle');
  const [tcUpdated, setTcUpdated] = useState(null);
  const [tcSource, setTcSource] = useState('');
  const fetchTC = useCallback(async (force = false) => {
    const KEY = 'ss_tc_cache';
    const today = new Date().toISOString().slice(0, 10);
    if (!force) {
      try {
        const c = JSON.parse(localStorage.getItem(KEY) || 'null');
        if (c && c.date === today && c.rate > 0) {
          setTcRate(c.rate);
          setTcUpdated(c.updated);
          setTcSource(c.source);
          setTcStatus('ok');
          if (force || !window.__config) setExchangeRate(c.rate);
          return;
        }
      } catch (e) {}
    }
    setTcStatus('loading');
    try {
      const r = await fetch('https://open.er-api.com/v6/latest/USD', {
        signal: AbortSignal.timeout(6000)
      });
      const d = await r.json();
      if (d.result === 'success' && d.rates?.MXN) {
        const rate = Math.round(d.rates.MXN * 100) / 100;
        const upd = new Date(d.time_last_update_utc).toLocaleString('es-MX', {
          day: '2-digit',
          month: 'short',
          hour: '2-digit',
          minute: '2-digit'
        });
        setTcRate(rate);
        setTcUpdated(upd);
        setTcSource('ExchangeRate-API');
        setTcStatus('ok');
        if (force || !window.__config) setExchangeRate(rate);
        localStorage.setItem(KEY, JSON.stringify({
          date: today,
          rate,
          updated: upd,
          source: 'ExchangeRate-API'
        }));
        return;
      }
    } catch (e) {}
    try {
      const r = await fetch('https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json', {
        signal: AbortSignal.timeout(6000)
      });
      const d = await r.json();
      if (d?.usd?.mxn) {
        const rate = Math.round(d.usd.mxn * 100) / 100;
        const upd = new Date().toLocaleString('es-MX', {
          day: '2-digit',
          month: 'short',
          hour: '2-digit',
          minute: '2-digit'
        });
        setTcRate(rate);
        setTcUpdated(upd);
        setTcSource('Fawazahmed0');
        setTcStatus('ok');
        if (force || !window.__config) setExchangeRate(rate);
        localStorage.setItem(KEY, JSON.stringify({
          date: today,
          rate,
          updated: upd,
          source: 'Fawazahmed0'
        }));
        return;
      }
    } catch (e) {}
    setTcStatus('error');
  }, []);
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ss_theme', theme);
  }, [theme]);
  useEffect(() => {
    loadXLSX();
    fetchTC();
    try {
      const p = window.__config || null;
      if (p) {
        if (p.exchangeRate) setExchangeRate(p.exchangeRate);
        if (p.mlGlobal) setMlGlobal(g => ({
          ...g,
          ...p.mlGlobal
        }));
        if (p.amzGlobal) setAmzGlobal(g => ({
          ...g,
          ...p.amzGlobal
        }));
        if (p.walGlobal) setWalGlobal(g => ({
          ...g,
          ...p.walGlobal
        }));
        if (p.mlCfgs) setMlCfgs(g => ({
          ...g,
          ...p.mlCfgs
        }));
        if (p.amzCfgs) setAmzCfgs(g => ({
          ...g,
          ...p.amzCfgs
        }));
        if (p.walCfgs) setWalCfgs(g => ({
          ...g,
          ...p.walCfgs
        }));
      }
    } catch (e) {}
  }, []);
  const saveSettings = async () => {
    if (!esAdmin) return;
    const datos = { exchangeRate, mlGlobal, amzGlobal, walGlobal, mlCfgs, amzCfgs, walCfgs };
    const r = await db.guardarConfig(datos, perfil.id);
    window.__config = datos;
    setAvisoDB(r.ok ? '' : 'No se pudo guardar la configuracion: ' + r.mensaje);
  };
  const calcPlat = (plat, price, costMXN, comPerc, ship) => {
    const g = plat === 'ml' ? mlGlobal : plat === 'amz' ? amzGlobal : walGlobal;
    const discP = g.discount || 0;
    const msiP = plat === 'amz' ? g.msi || 0 : 0;
    const taxAmt = price * (g.tax / 100);
    const msiAmt = price * (msiP / 100);
    const discAmt = price * (discP / 100);
    const baseCommAmt = price * (comPerc / 100);
    const effCom = comPerc - discP;
    const commTotal = price * (effCom / 100);
    const net = price - commTotal - msiAmt - taxAmt - ship;
    const profit = net * g.factor - costMXN;
    return {
      price,
      baseCommAmt,
      comAmt: commTotal,
      baseComPerc: comPerc,
      discAmt,
      msiAmt,
      taxAmt,
      taxPerc: g.tax,
      ship,
      profit,
      margin: price > 0 ? profit / price * 100 : 0,
      roi: costMXN > 0 ? profit / costMXN * 100 : 0,
      factor: g.factor,
      extraPerc: plat === 'amz' ? msiP : discP,
      costMXN
    };
  };
  const result = useMemo(() => {
    const cost = cn(simCost);
    const costMXN = simCostCur === 'USD' ? cost * exchangeRate : cost;
    const mlC = mlCfgs[simCat] || mlCfgs['GENERAL'];
    const amzC = amzCfgs[simCat] || amzCfgs['GENERAL'];
    const walC = walCfgs[simCat] || walCfgs['GENERAL'];
    const mlCom = simMLType === 'PREMIUM' ? mlC.premium : mlC.clasica;
    const r = {
      ml: calcPlat('ml', prices.ml, costMXN, mlCom, mlC.ship),
      amz: calcPlat('amz', prices.amz, costMXN, amzC.com, amzC.ship),
      wal: calcPlat('wal', prices.wal, costMXN, walC.com, walC.ship)
    };
    const pk = ['ml', 'amz', 'wal'];
    const mxP = Math.max(...pk.map(k => r[k].profit));
    const mnP = Math.min(...pk.map(k => r[k].profit));
    pk.forEach(k => {
      r[k]._win = r[k].profit === mxP && mxP > 0;
      r[k]._low = r[k].profit === mnP && r[k].profit >= 0 && mxP !== mnP;
    });
    return r;
  }, [simCost, simCostCur, exchangeRate, simCat, simMLType, prices, mlCfgs, amzCfgs, walCfgs, mlGlobal, amzGlobal, walGlobal]);
  const bProfit = Math.max(result.ml.profit, result.amz.profit, result.wal.profit);
  const bMargin = Math.max(result.ml.margin, result.amz.margin, result.wal.margin);
  const allNeg = result.ml.profit < 0 && result.amz.profit < 0 && result.wal.profit < 0;
  const hasData = prices.ml > 0 || prices.amz > 0 || prices.wal > 0;
  const hasCost = cn(simCost) > 0;
  const saveQuote = async () => {
    if (!simName || !hasCost) return;
    const costMXN = simCostCur === 'USD' ? cn(simCost) * exchangeRate : cn(simCost);
    const best = [{
      n: 'ML',
      p: result.ml.profit
    }, {
      n: 'AMZ',
      p: result.amz.profit
    }, {
      n: 'WAL',
      p: result.wal.profit
    }].reduce((a, b) => a.p > b.p ? a : b);
    const nueva = {
      name: simName,
      supplier: simSupplier.trim() || null,
      category: simCat,
      costMXN,
      originalCost: cn(simCost),
      originalCurrency: simCostCur,
      originalPrices: {
        ...prices
      },
      mlType: simMLType,
      bestPlatform: best.n,
      fullResults: {
        ml: result.ml,
        amz: result.amz,
        wal: result.wal
      }
    };
    const r = await db.guardarCotizacion(nueva, perfil);
    if (!r.ok) { setAvisoDB('No se pudo guardar en la base de datos: ' + r.mensaje); return; }
    setSavedQuotes(prev => [r.fila, ...prev]);
    setAvisoDB('');
  };
  const loadQuote = useCallback(q => {
    setSimName(q.name);
    setSimSupplier(q.supplier || '');
    setSimCost(q.originalCost);
    setSimCostCur(q.originalCurrency);
    if (mlCfgs[q.category]) setSimCat(q.category);
    setSimMLType(q.mlType || 'CLASICA');
    setPrices({
      ...q.originalPrices
    });
    setView('calc');
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }, [mlCfgs]);
  const deleteQuotes = useCallback(async ids => {
    const lista = [...ids];
    const r = await db.borrarCotizaciones(lista);
    if (!r.ok) { setAvisoDB('No se pudo borrar en la base de datos: ' + r.mensaje); return; }
    setSavedQuotes(p => p.filter(q => !ids.has(q.id)));
    setAvisoDB('');
  }, []);
  const downloadTemplate = async () => {
    const XLSX = await loadXLSX();
    const hd = ['NOMBRE DEL PRODUCTO', 'PROVEEDOR', 'COSTO DE PROVEEDOR', 'MONEDA COSTO (MXN/USD)', 'CATEGORIA DEL SCOUTING', 'PRECIO MERCADO LIBRE', 'TIPO PUBLICACION', 'PRECIO AMAZON', 'PRECIO WALMART'];
    const ex = ['Google - Pixel 10a (128GB)', 'Proveedor ABC', '459', 'USD', 'CELULARES', '12299', 'CLASICA', '12299', '12299'];
    const ws = XLSX.utils.aoa_to_sheet([hd, ex]);
    ws['!cols'] = [{
      wch: 30
    }, {
      wch: 20
    }, {
      wch: 22
    }, {
      wch: 25
    }, {
      wch: 25
    }, {
      wch: 22
    }, {
      wch: 20
    }, {
      wch: 18
    }, {
      wch: 18
    }];
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Productos');
    XLSX.writeFile(wb, 'Plantilla_SmartScouting.xlsx');
  };
  const handleUpload = async ev => {
    const file = ev.target.files[0];
    if (!file) return;
    setLoading(true);
    const XLSX = await loadXLSX();
    const reader = new FileReader();
    reader.onload = e => {
      try {
        const wb = XLSX.read(new Uint8Array(e.target.result), {
          type: 'array'
        });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json(ws, {
          header: 1
        });
        let hi = rows.findIndex(r => r && r.some(c => typeof c === 'string' && (c.toUpperCase().includes('NOMBRE') || c.toUpperCase().includes('TITULO'))));
        if (hi === -1) hi = 0;
        const hr = rows[hi] || [];
        const cm = {};
        hr.forEach((h, i) => {
          if (typeof h === 'string') cm[h.toUpperCase().trim()] = i;
        });
        const newQ = rows.slice(hi + 1).map((vals, idx) => {
          if (!vals || vals.length === 0 || !vals.some(v => v)) return null;
          const ni = cm['TITULO'] ?? cm['NOMBRE DEL PRODUCTO'] ?? cm['NOMBRE'] ?? 0;
          const si = cm['PROVEEDOR'] ?? cm['SUPPLIER'] ?? null;
          const ci = cm['CATEGORIA'] ?? cm['CATEGORIA DEL SCOUTING'] ?? 4;
          const cusdI = cm['COSTO USD'];
          const cmxnI = cm['COSTO MXN'];
          const cprovI = cm['COSTO DE PROVEEDOR'];
          const curI = cm['MONEDA COSTO (MXN/USD)'];
          const mlpI = cm['PRECIO'] ?? cm['PRECIO MERCADO LIBRE'] ?? 5;
          const mltI = cm['C O P'] ?? cm['TIPO PUBLICACION'] ?? 6;
          const azpI = cm['PRECIO AMAZON'] ?? 7;
          const wlpI = cm['PRECIO WALMART'] ?? 8;
          const name = vals[ni]?.toString() || 'Producto ' + (idx + 1);
          const supplier = si !== null && vals[si] ? vals[si].toString().trim() : null;
          const cat = vals[ci]?.toString().toUpperCase().trim() || 'GENERAL';
          let rawCost = 0,
            cur = 'MXN';
          if (cusdI !== undefined && vals[cusdI] !== undefined) {
            rawCost = cn(vals[cusdI]);
            cur = 'USD';
          } else if (cprovI !== undefined && vals[cprovI] !== undefined) {
            rawCost = cn(vals[cprovI]);
            cur = vals[curI] ? vals[curI].toString().toUpperCase().trim() : 'MXN';
          } else if (cmxnI !== undefined && vals[cmxnI] !== undefined) {
            rawCost = cn(vals[cmxnI]);
            cur = 'MXN';
          } else {
            rawCost = cn(vals[2]);
            cur = vals[3] ? vals[3].toString().toUpperCase().trim() : 'MXN';
          }
          const pML = cn(vals[mlpI]);
          const pAMZ = cn(vals[azpI]);
          const pWAL = cn(vals[wlpI]);
          let rowMLT = 'CLASICA';
          if (mltI !== undefined && vals[mltI] && vals[mltI].toString().toUpperCase().includes('PREMIUM')) rowMLT = 'PREMIUM';
          const costMXN = cur === 'USD' ? rawCost * exchangeRate : rawCost;
          const mlC = mlCfgs[cat] || mlCfgs['GENERAL'];
          const amzC = amzCfgs[cat] || amzCfgs['GENERAL'];
          const walC = walCfgs[cat] || walCfgs['GENERAL'];
          const mlCom = rowMLT === 'PREMIUM' ? mlC.premium : mlC.clasica;
          const rml = calcPlat('ml', pML, costMXN, mlCom, mlC.ship);
          const ramz = calcPlat('amz', pAMZ, costMXN, amzC.com, amzC.ship);
          const rwal = calcPlat('wal', pWAL, costMXN, walC.com, walC.ship);
          const best = [{
            n: 'ML',
            p: rml.profit
          }, {
            n: 'AMZ',
            p: ramz.profit
          }, {
            n: 'WAL',
            p: rwal.profit
          }].reduce((a, b) => a.p > b.p ? a : b);
          return {
            id: Date.now() + idx + Math.random(),
            name,
            supplier,
            category: cat,
            costMXN,
            originalCost: rawCost,
            originalCurrency: cur,
            originalPrices: {
              ml: pML,
              amz: pAMZ,
              wal: pWAL
            },
            mlType: rowMLT,
            bestPlatform: best.n,
            fullResults: {
              ml: rml,
              amz: ramz,
              wal: rwal
            }
          };
        }).filter(Boolean);
        setSavedQuotes(prev => [...newQ, ...prev]);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    reader.readAsArrayBuffer(file);
    ev.target.value = '';
  };
  const tcDif = tcStatus === 'ok' && tcRate && Math.abs(Number(exchangeRate) - tcRate) > 0.005;
  const NAV = [{
    id: 'calc',
    icon: /*#__PURE__*/React.createElement(Home, {
      size: 15
    }),
    label: 'Calculadora'
  }, {
    id: 'dashboard',
    icon: /*#__PURE__*/React.createElement(LayoutDashboard, {
      size: 15
    }),
    label: 'Dashboard',
    badge: savedQuotes.length || null
  }, {
    id: 'history',
    icon: /*#__PURE__*/React.createElement(Archive, {
      size: 15
    }),
    label: 'Historial',
    badge: savedQuotes.length || null
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      minHeight: '100vh',
      background: 'var(--bg)',
      display: 'flex',
      flexDirection: 'column'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      borderBottom: '0.5px solid var(--border)',
      background: 'var(--s1)',
      padding: '0 20px',
      height: 52,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      flexShrink: 0,
      boxShadow: 'var(--shadow)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 7
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 8,
      height: 8,
      borderRadius: '50%',
      background: 'var(--accent)'
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      fontWeight: 800,
      letterSpacing: '-.02em'
    }
  }, "SmartScouting")), esAdmin && /*#__PURE__*/React.createElement("a", {
    className: "volver",
    href: "panel.html",
    title: "Regresar al panel de administración"
  }, /*#__PURE__*/React.createElement(ArrowLeft, {
    size: 13
  }), "Panel"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 2
    }
  }, NAV.map(n => /*#__PURE__*/React.createElement("button", {
    key: n.id,
    className: 'nav-item' + (view === n.id ? ' active' : ''),
    onClick: () => setView(n.id),
    style: {
      position: 'relative'
    }
  }, n.icon, n.label, n.badge && /*#__PURE__*/React.createElement("span", {
    style: {
      position: 'absolute',
      top: 4,
      right: 4,
      width: 16,
      height: 16,
      borderRadius: '50%',
      background: 'var(--accent)',
      color: '#0D0F14',
      fontSize: 9,
      fontWeight: 800,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, n.badge > 99 ? '99+' : n.badge))))), /*#__PURE__*/React.createElement("div", {
  style: {
    display: 'flex',
    alignItems: 'center',
    gap: 10
  }
}, /*#__PURE__*/React.createElement("div", {
  className: "tc-pill",
  title: tcStatus === 'ok' && tcRate ? `Mercado hoy: ${tcRate.toFixed(2)} MXN por dolar (${tcSource}, ${tcUpdated}). En uso para los calculos: ${Number(exchangeRate).toFixed(2)} MXN.` + (tcDif ? ' Valor ajustado a mano desde Configuracion.' : '') : `En uso para los calculos: ${Number(exchangeRate).toFixed(2)} MXN por dolar.`
}, /*#__PURE__*/React.createElement("div", {
  className: "tc-seg"
}, /*#__PURE__*/React.createElement("div", {
  className: "tc-seg-hd"
}, /*#__PURE__*/React.createElement("span", {
  className: `tc-dot ${tcStatus}`
}), "Hoy"), /*#__PURE__*/React.createElement("div", {
  className: "tc-seg-bd"
}, tcStatus === 'ok' && tcRate ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
  className: "tc-val"
}, tcRate.toFixed(2)), /*#__PURE__*/React.createElement("span", {
  className: "tc-cur"
}, "MXN")) : tcStatus === 'loading' ? /*#__PURE__*/React.createElement("span", {
  className: "tc-mut"
}, "Cargando…") : /*#__PURE__*/React.createElement("span", {
  className: "tc-mut"
}, "Sin dato"))), /*#__PURE__*/React.createElement("div", {
  className: "tc-div"
}), /*#__PURE__*/React.createElement("div", {
  className: "tc-seg"
}, /*#__PURE__*/React.createElement("div", {
  className: "tc-seg-hd"
}, tcDif ? 'Configurado' : 'En uso'), /*#__PURE__*/React.createElement("div", {
  className: "tc-seg-bd"
}, /*#__PURE__*/React.createElement("span", {
  className: 'tc-val' + (tcDif ? ' warn' : '')
}, Number(exchangeRate).toFixed(2)), /*#__PURE__*/React.createElement("span", {
  className: "tc-cur"
}, "MXN")))), /*#__PURE__*/React.createElement("div", {
  className: "tb-grupo",
  title: "Carga y descarga de productos en Excel"
}, /*#__PURE__*/React.createElement("button", {
  className: "tb-btn",
  onClick: downloadTemplate
}, /*#__PURE__*/React.createElement(Download, {
  size: 13
}), "Plantilla"), /*#__PURE__*/React.createElement("div", {
  className: "tb-gdiv"
}), /*#__PURE__*/React.createElement("label", {
  className: "tb-btn",
  style: {
    cursor: 'pointer'
  }
}, /*#__PURE__*/React.createElement(Upload, {
  size: 13
}), "Importar", /*#__PURE__*/React.createElement("input", {
  type: "file",
  accept: ".xlsx,.xls",
  style: {
    display: 'none'
  },
  onChange: handleUpload
}))), /*#__PURE__*/React.createElement("div", {
  className: "tb-grupo"
}, /*#__PURE__*/React.createElement("button", {
  className: "tb-btn",
  onClick: () => setShowSettings(true),
  title: esAdmin ? 'Comisiones, variables y tipo de cambio' : 'Consultar comisiones y variables'
}, /*#__PURE__*/React.createElement(Settings, {
  size: 13
}), esAdmin ? 'Configuración' : 'Comisiones'), /*#__PURE__*/React.createElement("div", {
  className: "tb-gdiv"
}), /*#__PURE__*/React.createElement("button", {
  className: "tb-btn tb-icon",
  onClick: () => setTheme(t => t === 'dark' ? 'light' : 'dark'),
  title: theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'
}, theme === 'dark' ? /*#__PURE__*/React.createElement(Sun, {
  size: 14
}) : /*#__PURE__*/React.createElement(Moon, {
  size: 14
}))), /*#__PURE__*/React.createElement("div", {
  className: "tb-grupo cuenta"
}, /*#__PURE__*/React.createElement("div", {
  className: "user-pill",
  title: perfil.correo || ''
}, /*#__PURE__*/React.createElement("div", {
  className: "user-av"
}, ((perfil.nombre[0] || '') + (perfil.apellidos[0] || '')).toUpperCase() || '··'), /*#__PURE__*/React.createElement("span", {
  style: {
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--t2)'
  }
}, perfil.nombre), /*#__PURE__*/React.createElement("span", {
  className: 'rol-tag ' + (esAdmin ? 'admin' : 'scouting')
}, esAdmin ? 'Admin' : 'Scouting')), /*#__PURE__*/React.createElement("div", {
  className: "tb-gdiv"
}), /*#__PURE__*/React.createElement("button", {
  className: "tb-btn tb-icon salir",
  title: "Cerrar sesión",
  onClick: async () => {
    await db.salir();
    location.replace('index.html');
  }
}, /*#__PURE__*/React.createElement(LogOut, {
  size: 14
}))))), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, view === 'calc' && /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1320,
      margin: '0 auto',
      padding: '20px 24px'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "card",
    style: {
      padding: '16px 20px',
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "sec-ttl"
  }, "Datos del producto"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '2fr 1.2fr 1fr 1fr 1.1fr',
      gap: 12,
      alignItems: 'end'
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "lbl"
  }, /*#__PURE__*/React.createElement(Package, {
    size: 12
  }), "Nombre del producto"), /*#__PURE__*/React.createElement("div", {
    className: "fw"
  }, /*#__PURE__*/React.createElement("input", {
    type: "text",
    value: simName,
    onChange: e => setSimName(e.target.value),
    placeholder: "Ej. Google Pixel 10a 128GB",
    style: {
      height: 36,
      padding: '0 12px',
      fontFamily: 'var(--sans)'
    }
  }))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "lbl"
  }, /*#__PURE__*/React.createElement(Building2, {
    size: 12
  }), "Proveedor"), /*#__PURE__*/React.createElement("div", {
    className: "fw"
  }, /*#__PURE__*/React.createElement("input", {
    type: "text",
    value: simSupplier,
    onChange: e => setSimSupplier(e.target.value),
    placeholder: "Ej. Importadora XYZ",
    style: {
      height: 36,
      padding: '0 12px',
      fontFamily: 'var(--sans)'
    }
  }))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "lbl"
  }, /*#__PURE__*/React.createElement(DollarSign, {
    size: 12
  }), "Costo del producto"), /*#__PURE__*/React.createElement("div", {
    className: "fw"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fpre"
  }, "$"), /*#__PURE__*/React.createElement("input", {
    type: "number",
    value: simCost,
    onChange: e => setSimCost(e.target.value),
    placeholder: "0"
  }), /*#__PURE__*/React.createElement("span", {
    className: 'fsuf' + (simCostCur === 'USD' && cn(simCost) > 0 ? ' conv' : '')
  }, simCostCur === 'USD' && cn(simCost) > 0 ? '≈ ' + fmt(cn(simCost) * exchangeRate) : simCostCur))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "lbl"
  }, "Divisa"), /*#__PURE__*/React.createElement("div", {
    className: "seg"
  }, /*#__PURE__*/React.createElement("button", {
    className: simCostCur === 'MXN' ? 'on' : '',
    onClick: () => setSimCostCur('MXN')
  }, "MXN"), /*#__PURE__*/React.createElement("button", {
    className: simCostCur === 'USD' ? 'on' : '',
    onClick: () => setSimCostCur('USD')
  }, "USD"))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "lbl"
  }, /*#__PURE__*/React.createElement(Tags, {
    size: 12
  }), "Categoría"), /*#__PURE__*/React.createElement("select", {
    className: "sel",
    value: simCat,
    onChange: e => setSimCat(e.target.value)
  }, Object.keys(mlCfgs).sort().map(c => /*#__PURE__*/React.createElement("option", {
    key: c,
    value: c
  }, c)))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr 1fr',
      gap: 12,
      marginBottom: 12
    }
  }, ['ml', 'amz', 'wal'].map(k => /*#__PURE__*/React.createElement(PlatCard, {
    key: k,
    id: k,
    name: PI[k].name,
    logo: PI[k].logo,
    color: PI[k].color,
    res: result[k],
    showMLToggle: k === 'ml',
    mlType: simMLType,
    onMLTypeChange: setSimMLType,
    onPChange: v => setPrices(p => ({
      ...p,
      [k]: v
    }))
  }))), hasData && hasCost && /*#__PURE__*/React.createElement("div", {
    style: {
      background: allNeg ? 'var(--dn-dim)' : 'var(--s1)',
      border: `0.5px solid ${allNeg ? 'var(--dn-b)' : 'var(--border)'}`,
      borderRadius: 12,
      padding: '14px 20px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 36,
      height: 36,
      borderRadius: 8,
      background: allNeg ? 'var(--dn-dim)' : 'var(--ac-dim)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, allNeg ? /*#__PURE__*/React.createElement(AlertCircle, {
    size: 18,
    color: "var(--danger)"
  }) : /*#__PURE__*/React.createElement(Zap, {
    size: 18,
    color: "var(--accent)"
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--t3)',
      textTransform: 'uppercase',
      letterSpacing: '.06em',
      marginBottom: 2
    }
  }, allNeg ? 'Pérdida en todas las plataformas' : 'Utilidad máxima proyectada'), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 20,
      fontWeight: 700,
      fontFamily: 'var(--mono)',
      color: allNeg ? 'var(--danger)' : 'var(--t1)'
    }
  }, fmt(bProfit)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 20,
      alignItems: 'center'
    }
  }, simSupplier && /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'right'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--t3)',
      textTransform: 'uppercase',
      letterSpacing: '.06em',
      marginBottom: 3
    }
  }, "Proveedor"), /*#__PURE__*/React.createElement("span", {
    className: "prov-tag"
  }, /*#__PURE__*/React.createElement(Building2, {
    size: 11
  }), simSupplier)), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'right'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: 'var(--t3)',
      textTransform: 'uppercase',
      letterSpacing: '.06em',
      marginBottom: 2
    }
  }, "Mejor margen"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 20,
      fontWeight: 700,
      fontFamily: 'var(--mono)',
      color: allNeg ? 'var(--danger)' : 'var(--accent)'
    }
  }, fmt(bMargin) + '%')), /*#__PURE__*/React.createElement("button", {
    className: "btn bp",
    style: {
      height: 38,
      padding: '0 18px'
    },
    onClick: saveQuote,
    disabled: !simName || !hasCost
  }, /*#__PURE__*/React.createElement(Save, {
    size: 14
  }), "Guardar escenario"))), !hasData && /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'center',
      padding: '10px 0',
      color: 'var(--t3)',
      fontSize: 12
    }
  }, "Ingresa el precio de venta en cada plataforma para ver el análisis.")), view === 'dashboard' && /*#__PURE__*/React.createElement(Dashboard, {
    quotes: savedQuotes,
    onLoad: loadQuote,
    onDelete: deleteQuotes
  }), view === 'history' && /*#__PURE__*/React.createElement(History, {
    quotes: savedQuotes,
    onLoad: loadQuote,
    onDelete: deleteQuotes
  })), /*#__PURE__*/React.createElement(SettingsModal, {
    show: showSettings,
    onClose: () => setShowSettings(false),
    exchangeRate: exchangeRate,
    setExchangeRate: setExchangeRate,
    mlGlobal: mlGlobal,
    setMlGlobal: setMlGlobal,
    amzGlobal: amzGlobal,
    setAmzGlobal: setAmzGlobal,
    walGlobal: walGlobal,
    setWalGlobal: setWalGlobal,
    mlCfgs: mlCfgs,
    setMlCfgs: setMlCfgs,
    amzCfgs: amzCfgs,
    setAmzCfgs: setAmzCfgs,
    walCfgs: walCfgs,
    setWalCfgs: setWalCfgs,
    onSave: saveSettings,
    tcStatus: tcStatus,
    tcRate: tcRate,
    tcUpdated: tcUpdated,
    tcSource: tcSource,
    fetchTC: fetchTC
  }), loading && /*#__PURE__*/React.createElement("div", {
    className: "mo"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: 'var(--s1)',
      border: '0.5px solid var(--border-s)',
      borderRadius: 16,
      padding: '40px 60px',
      textAlign: 'center',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "sp"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      fontWeight: 700,
      textTransform: 'uppercase',
      letterSpacing: '.06em'
    }
  }, "Procesando archivo…"))));
}
/* ═══ ARRANQUE ═══
   Antes de dibujar nada: comprobar la sesion contra la base de datos,
   traer la configuracion compartida y las cotizaciones que corresponden. */
(async () => {
  const raiz = document.getElementById('root');
  const perfil = await db.proteger();
  if (!perfil) return;

  window.__perfil = perfil;
  window.__config = await db.leerConfig();
  if (window.__config && Object.keys(window.__config).length === 0) window.__config = null;

  const cot = await db.listarCotizaciones();
  window.__cotizaciones = cot.filas;

  ReactDOM.createRoot(raiz).render(/*#__PURE__*/React.createElement(App, null));

  if (!cot.ok) {
    const d = document.createElement('div');
    d.className = 'aviso-db';
    d.textContent = 'No se pudieron cargar las cotizaciones: ' + cot.mensaje;
    document.body.appendChild(d);
  }
})();