import React, { useState, useEffect } from 'react';
import { 
  MessageSquare, LayoutDashboard, FileSpreadsheet, ShieldAlert, 
  Award, FileText, CheckCircle2, AlertTriangle, ArrowRight, 
  Download, Upload, RefreshCw, Send, Building2, Clock, DollarSign
} from 'lucide-react';

interface ChatMsg {
  role: 'user' | 'assistant';
  content: string;
  parsed_pr?: any;
}

interface RequirementItem {
  group_id: string;
  resolved_item_code: string;
  decision: string;
  route: string;
  po_id?: string;
  supplier_id?: string;
  unit_price?: number;
  group_value_inr: number;
  suggested_supplier_ids?: string;
  policy_version: string;
  reason: string;
  status: string;
  pr_lines: { pr_no: string; pr_line: number }[];
  audit_trail: any[];
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'buyer' | 'batch' | 'policy' | 'suppliers' | 'contracts'>('chat');
  const [activePolicyVersion, setActivePolicyVersion] = useState<string>('5.0');
  
  // Chat state
  const [messages, setMessages] = useState<ChatMsg[]>([
    {
      role: 'assistant',
      content: 'Welcome to **Corvo Engineering Procurement Assistant**.\nI can help you raise purchase requests following Procurement Policy v5.0.\n\nType your requirement (e.g. *"need 200 nitrile gloves for Chakan by next Friday"*) or use the quick chips below.'
    }
  ]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [currentParsedPR, setCurrentParsedPR] = useState<any>(null);
  const [submittedDecision, setSubmittedDecision] = useState<any>(null);

  // Buyer Workspace state
  const [requirements, setRequirements] = useState<RequirementItem[]>([]);
  const [buyerSummary, setBuyerSummary] = useState<any>({});
  const [routeFilter, setRouteFilter] = useState<string>('ALL');
  const [plantFilter, setPlantFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedReqForOverride, setSelectedReqForOverride] = useState<RequirementItem | null>(null);
  const [overrideComment, setOverrideComment] = useState('');
  const [overrideRoute, setOverrideRoute] = useState('SPOT_PO');

  // Batch Processor state
  const [batchFile, setBatchFile] = useState<File | null>(null);
  const [batchLoading, setBatchLoading] = useState(false);
  const [batchResult, setBatchResult] = useState<any>(null);

  // Policy state
  const [currentPolicy, setCurrentPolicy] = useState<any>(null);
  const [amendmentText, setAmendmentText] = useState('');
  const [amendmentFile, setAmendmentFile] = useState<File | null>(null);
  const [amendmentDiff, setAmendmentDiff] = useState<any>(null);
  const [policyLoading, setPolicyLoading] = useState(false);

  // Preferred suppliers state
  const [prefDate, setPrefDate] = useState('2026-11-01');
  const [preferredItems, setPreferredItems] = useState<any>({});
  const [selectedItemCode, setSelectedItemCode] = useState<string>('');

  // Contracts state
  const [contractsList, setContractsList] = useState<any[]>([]);

  // Fetch initial data
  useEffect(() => {
    fetchCurrentPolicy();
    fetchBuyerRequirements();
    fetchContracts();
    fetchPreferredSuppliers('2026-11-01');
  }, []);

  const fetchCurrentPolicy = async () => {
    try {
      const res = await fetch('/api/policy/current');
      if (res.ok) {
        const data = await res.json();
        setCurrentPolicy(data);
        setActivePolicyVersion(data.version);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchBuyerRequirements = async () => {
    try {
      const res = await fetch('/api/buyer/requirements');
      if (res.ok) {
        const data = await res.json();
        setRequirements(data.requirements || []);
        setBuyerSummary(data.summary || {});
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchContracts = async () => {
    try {
      const res = await fetch('/api/contracts');
      if (res.ok) {
        const data = await res.json();
        setContractsList(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchPreferredSuppliers = async (date: string) => {
    try {
      const res = await fetch(`/api/suppliers/preferred?date=${date}`);
      if (res.ok) {
        const data = await res.json();
        setPreferredItems(data.items || {});
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Chat Handlers
  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputPrompt;
    if (!text.trim()) return;

    const userMsg: ChatMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInputPrompt('');
    setChatLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: 'user', content: text, metadata: currentParsedPR })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply, parsed_pr: data.parsed_pr }]);
      setCurrentParsedPR(data.parsed_pr);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Connection error. Please try again.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleConfirmPR = async () => {
    if (!currentParsedPR) return;
    setChatLoading(true);
    try {
      const res = await fetch('/api/pr/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentParsedPR)
      });
      const data = await res.json();
      setSubmittedDecision(data.decision);
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `🎉 **Purchase Requisition Confirmed!**\n\n- **PR Number:** \`${data.pr.pr_no}\`\n- **Requirement Group:** \`${data.decision.group_id}\`\n- **Decision:** **${data.decision.decision}** (Route: \`${data.decision.route}\`)\n- **Assigned Value:** ₹${data.decision.group_value_inr.toLocaleString()}\n- **Reason:** ${data.decision.reason}`
        }
      ]);
      fetchBuyerRequirements();
    } catch (err) {
      alert('Failed to submit PR');
    } finally {
      setChatLoading(false);
    }
  };

  // Buyer Actions
  const handleApproveReq = async (groupId: string) => {
    try {
      const res = await fetch('/api/buyer/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ group_id: groupId, buyer_name: 'Lead Buyer (Corvo)' })
      });
      if (res.ok) {
        fetchBuyerRequirements();
      }
    } catch (err) {
      alert('Error approving requirement');
    }
  };

  const handleOverrideReq = async () => {
    if (!selectedReqForOverride || !overrideComment.trim()) {
      alert('A written reason comment is mandatory for overrides (Policy 8.1).');
      return;
    }
    try {
      const res = await fetch('/api/buyer/override', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          group_id: selectedReqForOverride.group_id,
          override_route: overrideRoute,
          override_comment: overrideComment,
          buyer_name: 'Lead Buyer (Corvo)'
        })
      });
      if (res.ok) {
        setSelectedReqForOverride(null);
        setOverrideComment('');
        fetchBuyerRequirements();
      }
    } catch (err) {
      alert('Error recording override');
    }
  };

  // Batch Processor
  const handleProcessBatch = async () => {
    if (!batchFile) return;
    setBatchLoading(true);
    const formData = new FormData();
    formData.append('file', batchFile);

    try {
      const res = await fetch('/api/process-batch', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setBatchResult(data);
      fetchBuyerRequirements();
    } catch (err) {
      alert('Failed to process batch CSV');
    } finally {
      setBatchLoading(false);
    }
  };

  // Policy Amendment
  const handlePreviewAmendment = async () => {
    setPolicyLoading(true);
    try {
      if (amendmentFile) {
        const formData = new FormData();
        formData.append('file', amendmentFile);
        const res = await fetch('/api/policy/amend-upload', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        setAmendmentDiff(data);
      } else if (amendmentText.trim()) {
        const res = await fetch('/api/policy/amend-text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ amendment_text: amendmentText })
        });
        const data = await res.json();
        setAmendmentDiff(data);
      }
    } catch (err) {
      alert('Error parsing amendment');
    } finally {
      setPolicyLoading(false);
    }
  };

  const handleApproveAmendment = async (version: string) => {
    setPolicyLoading(true);
    try {
      const res = await fetch('/api/policy/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ version })
      });
      if (res.ok) {
        alert(`Policy version ${version} approved and active!`);
        setAmendmentDiff(null);
        setAmendmentText('');
        setAmendmentFile(null);
        fetchCurrentPolicy();
      }
    } catch (err) {
      alert('Failed to approve policy amendment');
    } finally {
      setPolicyLoading(false);
    }
  };

  // Route Badge Helper
  const renderRouteBadge = (route: string) => {
    switch (route) {
      case 'CONTRACT_PO':
        return <span className="badge badge-blue">CONTRACT PO</span>;
      case 'SPOT_PO':
        return <span className="badge badge-emerald">SPOT PO</span>;
      case 'EMERGENCY_PO':
        return <span className="badge badge-amber">EMERGENCY PO</span>;
      case 'RFQ':
        return <span className="badge badge-purple">RFQ SOURCING</span>;
      case 'RFP':
        return <span className="badge badge-cyan">RFP SOURCING</span>;
      case 'CAPEX_SOURCING':
        return <span className="badge badge-rose">CAPEX SOURCING</span>;
      case 'NEW_ITEM_SOURCING':
        return <span className="badge badge-dim">NEW ITEM SOURCING</span>;
      default:
        return <span className="badge badge-dim">{route}</span>;
    }
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-logo">C</div>
          <div>
            <div className="brand-title">Corvo Engineering</div>
            <div className="brand-subtitle">Policy-Driven PR-to-PO Decision Engine</div>
          </div>
        </div>

        <div className="header-badges">
          <span className="badge badge-emerald">
            <CheckCircle2 size={13} /> Active Policy: v{activePolicyVersion}
          </span>
          <span className="badge badge-blue">
            <Building2 size={13} /> Plants: PUN1 & CHK1
          </span>
        </div>
      </header>

      {/* Main Navigation Tabs */}
      <nav className="nav-bar">
        <button 
          className={`nav-tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          <MessageSquare size={17} /> Chat Intake
        </button>
        <button 
          className={`nav-tab ${activeTab === 'buyer' ? 'active' : ''}`}
          onClick={() => setActiveTab('buyer')}
        >
          <LayoutDashboard size={17} /> Buyer Workspace
        </button>
        <button 
          className={`nav-tab ${activeTab === 'batch' ? 'active' : ''}`}
          onClick={() => setActiveTab('batch')}
        >
          <FileSpreadsheet size={17} /> Batch Processor & Blind Test
        </button>
        <button 
          className={`nav-tab ${activeTab === 'policy' ? 'active' : ''}`}
          onClick={() => setActiveTab('policy')}
        >
          <ShieldAlert size={17} /> Policy as Data
        </button>
        <button 
          className={`nav-tab ${activeTab === 'suppliers' ? 'active' : ''}`}
          onClick={() => setActiveTab('suppliers')}
        >
          <Award size={17} /> Preferred Suppliers
        </button>
        <button 
          className={`nav-tab ${activeTab === 'contracts' ? 'active' : ''}`}
          onClick={() => setActiveTab('contracts')}
        >
          <FileText size={17} /> Contracts Register
        </button>
      </nav>

      {/* Main Body Content */}
      <main className="main-content">
        {/* 1. CHAT INTAKE TAB */}
        {activeTab === 'chat' && (
          <div className="chat-layout">
            <div className="chat-box">
              <div className="chat-messages">
                {messages.map((m, idx) => (
                  <div key={idx} className={`chat-bubble ${m.role === 'user' ? 'bubble-user' : 'bubble-assistant'}`}>
                    <div style={{ whiteSpace: 'pre-wrap' }}>{m.content}</div>
                  </div>
                ))}
              </div>

              <div style={{ padding: '0 1rem 0.5rem 1rem' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '0.25rem' }}>Quick Examples:</div>
                <div className="quick-chips">
                  <div className="chip" onClick={() => handleSendMessage("need 200 nitrile gloves for Chakan by next Friday")}>
                    "need 200 nitrile gloves for Chakan by next Friday"
                  </div>
                  <div className="chip" onClick={() => handleSendMessage("need 15 nos MS sheet 3mm for Bhosari by 2026-11-15")}>
                    "15 nos MS sheet 3mm for Bhosari"
                  </div>
                  <div className="chip" onClick={() => handleSendMessage("urgent 2380 nos gearbox oil seal for Bhosari")}>
                    "urgent gearbox oil seal for Bhosari"
                  </div>
                  <div className="chip" onClick={() => handleSendMessage("need 4 nos eot crane 5 ton for Bhosari")}>
                    "eot crane 5 ton (Capex)"
                  </div>
                </div>
              </div>

              <div className="chat-input-row">
                <input 
                  type="text"
                  className="chat-input"
                  placeholder="Type a procurement request (e.g. need 100 kg EN8 round bar for PUN1)..."
                  value={inputPrompt}
                  onChange={(e) => setInputPrompt(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                />
                <button className="btn btn-primary" onClick={() => handleSendMessage()} disabled={chatLoading}>
                  <Send size={16} /> Send
                </button>
              </div>
            </div>

            {/* Live PR Preview Card */}
            <div>
              <div className="card">
                <div className="card-header">
                  <div className="card-title">
                    <FileText size={18} color="var(--accent-cyan)" /> Structured PR Card
                  </div>
                  {currentParsedPR && (
                    <span className="badge badge-emerald">
                      {currentParsedPR.missing_fields?.length === 0 ? 'Ready to Submit' : 'Incomplete'}
                    </span>
                  )}
                </div>

                {currentParsedPR ? (
                  <div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.85rem' }}>
                      <div>
                        <span style={{ color: 'var(--text-dim)', display: 'block' }}>Item Code:</span>
                        <code style={{ color: 'var(--accent-cyan)' }}>{currentParsedPR.item_code || 'Pending'}</code>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-dim)', display: 'block' }}>Plant:</span>
                        <strong>{currentParsedPR.plant || 'Pending'}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-dim)', display: 'block' }}>Quantity:</span>
                        <strong>{currentParsedPR.quantity ? `${currentParsedPR.quantity} ${currentParsedPR.uom}` : 'Pending'}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-dim)', display: 'block' }}>Urgency:</span>
                        <span className={`badge ${currentParsedPR.urgency === 'Emergency' ? 'badge-amber' : 'badge-dim'}`}>
                          {currentParsedPR.urgency}
                        </span>
                      </div>
                      <div style={{ gridColumn: 'span 2' }}>
                        <span style={{ color: 'var(--text-dim)', display: 'block' }}>Description:</span>
                        <strong>{currentParsedPR.description || 'Pending'}</strong>
                      </div>
                      <div style={{ gridColumn: 'span 2' }}>
                        <span style={{ color: 'var(--text-dim)', display: 'block' }}>Need-By Date:</span>
                        <strong>{currentParsedPR.need_by_date || 'Pending'}</strong>
                      </div>
                    </div>

                    {currentParsedPR.missing_fields?.length > 0 && (
                      <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem', color: '#fbbf24' }}>
                        <AlertTriangle size={14} style={{ display: 'inline', marginRight: '4px' }} />
                        Missing: {currentParsedPR.missing_fields.join(', ')}
                      </div>
                    )}

                    {currentParsedPR.missing_fields?.length === 0 && (
                      <button 
                        className="btn btn-success" 
                        style={{ width: '100%', marginTop: '1.25rem' }}
                        onClick={handleConfirmPR}
                        disabled={chatLoading}
                      >
                        <CheckCircle2 size={16} /> Confirm & Submit PR
                      </button>
                    )}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text-dim)', fontSize: '0.875rem' }}>
                    Type your request in the chat to auto-generate the PR preview card.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* 2. BUYER WORKSPACE TAB */}
        {activeTab === 'buyer' && (
          <div>
            {/* Top KPI row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
              <div className="card" style={{ marginBottom: 0, padding: '1.25rem' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Total Requirements</div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#fff', marginTop: '0.25rem' }}>
                  {buyerSummary.total_requirements || requirements.length}
                </div>
              </div>
              <div className="card" style={{ marginBottom: 0, padding: '1.25rem' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Direct POs</div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--accent-emerald)', marginTop: '0.25rem' }}>
                  {buyerSummary.total_pos || 0}
                </div>
              </div>
              <div className="card" style={{ marginBottom: 0, padding: '1.25rem' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Sourcing Events (RFQ/RFP)</div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--accent-purple)', marginTop: '0.25rem' }}>
                  {buyerSummary.total_sourcing || 0}
                </div>
              </div>
              <div className="card" style={{ marginBottom: 0, padding: '1.25rem' }}>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Total Value (INR)</div>
                <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--accent-cyan)', marginTop: '0.25rem' }}>
                  ₹{(buyerSummary.total_value || 0).toLocaleString()}
                </div>
              </div>
            </div>

            {/* Filter controls */}
            <div className="card" style={{ padding: '1rem', marginBottom: '1.5rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
              <input 
                type="text" 
                placeholder="Search Item code, supplier or group..." 
                className="chat-input"
                style={{ maxWidth: '300px' }}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <select 
                className="chat-input" 
                style={{ maxWidth: '200px' }}
                value={routeFilter}
                onChange={(e) => setRouteFilter(e.target.value)}
              >
                <option value="ALL">All Routes</option>
                <option value="CONTRACT_PO">Contract PO</option>
                <option value="SPOT_PO">Spot PO</option>
                <option value="EMERGENCY_PO">Emergency PO</option>
                <option value="RFQ">RFQ</option>
                <option value="RFP">RFP</option>
                <option value="CAPEX_SOURCING">Capex Sourcing</option>
              </select>
              <button className="btn btn-secondary btn-sm" onClick={fetchBuyerRequirements}>
                <RefreshCw size={14} /> Refresh
              </button>
            </div>

            {/* Requirements Table */}
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Group ID</th>
                    <th>PR Lines</th>
                    <th>Item</th>
                    <th>Route</th>
                    <th>Assigned Supplier</th>
                    <th>Requirement Value</th>
                    <th>Policy Clause Reason</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {requirements.filter(r => {
                    if (routeFilter !== 'ALL' && r.route !== routeFilter) return false;
                    if (searchQuery && !r.resolved_item_code.toLowerCase().includes(searchQuery.toLowerCase()) && !r.group_id.toLowerCase().includes(searchQuery.toLowerCase())) return false;
                    return true;
                  }).map((req, i) => (
                    <tr key={i}>
                      <td><code style={{ color: 'var(--accent-cyan)' }}>{req.group_id}</code></td>
                      <td>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          {req.pr_lines.map(p => `${p.pr_no}/${p.pr_line}`).join(', ')}
                        </span>
                      </td>
                      <td><strong>{req.resolved_item_code}</strong></td>
                      <td>{renderRouteBadge(req.route)}</td>
                      <td>
                        {req.supplier_id ? (
                          <span style={{ fontWeight: 600, color: '#fff' }}>{req.supplier_id}</span>
                        ) : (
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                            Suggested: {req.suggested_supplier_ids || 'None'}
                          </span>
                        )}
                      </td>
                      <td style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>
                        ₹{req.group_value_inr.toLocaleString()}
                      </td>
                      <td style={{ fontSize: '0.8rem', maxWidth: '320px', color: 'var(--text-muted)' }}>
                        {req.reason}
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '0.4rem' }}>
                          <button 
                            className="btn btn-success btn-sm" 
                            title="1-Click Approve"
                            onClick={() => handleApproveReq(req.group_id)}
                          >
                            Approve
                          </button>
                          <button 
                            className="btn btn-outline btn-sm"
                            title="Override decision with written justification"
                            onClick={() => setSelectedReqForOverride(req)}
                          >
                            Override
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Override Modal */}
            {selectedReqForOverride && (
              <div className="modal-overlay">
                <div className="modal-content">
                  <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <ShieldAlert size={20} color="var(--accent-amber)" /> Override Requirement {selectedReqForOverride.group_id}
                  </h3>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                    Policy Clause 8.1 requires a formal written justification for any procurement decision override.
                  </p>

                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ fontSize: '0.8rem', display: 'block', marginBottom: '0.25rem' }}>Select Target Route:</label>
                    <select 
                      className="chat-input" 
                      style={{ width: '100%' }}
                      value={overrideRoute}
                      onChange={(e) => setOverrideRoute(e.target.value)}
                    >
                      <option value="SPOT_PO">Spot PO</option>
                      <option value="CONTRACT_PO">Contract PO</option>
                      <option value="EMERGENCY_PO">Emergency PO</option>
                      <option value="RFQ">RFQ Sourcing</option>
                      <option value="RFP">RFP Sourcing</option>
                    </select>
                  </div>

                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ fontSize: '0.8rem', display: 'block', marginBottom: '0.25rem' }}>Written Justification (Mandatory):</label>
                    <textarea 
                      className="chat-input"
                      style={{ width: '100%', height: '80px' }}
                      placeholder="e.g. Critical plant maintenance requirement approved by VP of Operations..."
                      value={overrideComment}
                      onChange={(e) => setOverrideComment(e.target.value)}
                    />
                  </div>

                  <div className="modal-actions">
                    <button className="btn btn-secondary" onClick={() => setSelectedReqForOverride(null)}>Cancel</button>
                    <button className="btn btn-primary" onClick={handleOverrideReq}>Submit Override</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 3. BATCH PROCESSOR TAB */}
        {activeTab === 'batch' && (
          <div>
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <FileSpreadsheet size={20} color="var(--accent-cyan)" /> Batch PR Processor (Task Section 3.7)
                </div>
                <span className="badge badge-blue">Blind-Test Engine</span>
              </div>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                Upload a PR batch CSV (e.g. <code>sample_pr_batch.csv</code> or blind-test test set) to execute the decision engine.
              </p>

              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
                <input 
                  type="file" 
                  accept=".csv"
                  className="chat-input"
                  style={{ maxWidth: '350px' }}
                  onChange={(e) => setBatchFile(e.target.files ? e.target.files[0] : null)}
                />
                <button 
                  className="btn btn-primary" 
                  onClick={handleProcessBatch}
                  disabled={!batchFile || batchLoading}
                >
                  {batchLoading ? <RefreshCw className="animate-spin" size={16} /> : <Upload size={16} />}
                  Process Batch CSV
                </button>

                <a href="/api/export-decisions" download className="btn btn-success" style={{ marginLeft: 'auto' }}>
                  <Download size={16} /> Export Decisions CSV
                </a>
              </div>

              {batchResult && (
                <div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
                    <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: 'var(--radius-md)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Lines Processed</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800 }}>{batchResult.total_lines}</div>
                    </div>
                    <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: 'var(--radius-md)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Requirement Groups</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>{batchResult.unique_requirements}</div>
                    </div>
                    <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: 'var(--radius-md)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Consolidated POs (24h)</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>{batchResult.consolidated_pos}</div>
                    </div>
                    <div style={{ padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: 'var(--radius-md)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Total Spend (INR)</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-amber)' }}>₹{batchResult.total_value_inr.toLocaleString()}</div>
                    </div>
                  </div>

                  <h4 style={{ marginBottom: '0.75rem' }}>Route Breakdown:</h4>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {Object.entries(batchResult.route_distribution).map(([route, count]: any) => (
                      <div key={route} style={{ padding: '0.5rem 0.85rem', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        {renderRouteBadge(route)}
                        <strong style={{ fontSize: '0.9rem' }}>{count}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 4. POLICY AS DATA TAB */}
        {activeTab === 'policy' && (
          <div>
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <ShieldAlert size={20} color="var(--accent-cyan)" /> Active Policy Engine (Version {activePolicyVersion})
                </div>
                <span className="badge badge-emerald">Zero Code Updates Required</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                <div>
                  <h4 style={{ marginBottom: '0.75rem' }}>Submit Policy Amendment (Blind Test Ready)</h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1rem' }}>
                    Type the revision in natural language or upload the amendment PDF sent by Cantill.
                  </p>

                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ fontSize: '0.8rem', display: 'block', marginBottom: '0.35rem' }}>Upload Amendment Document (PDF/TXT):</label>
                    <input 
                      type="file" 
                      accept=".pdf,.txt"
                      className="chat-input"
                      style={{ width: '100%' }}
                      onChange={(e) => setAmendmentFile(e.target.files ? e.target.files[0] : null)}
                    />
                  </div>

                  <div style={{ marginBottom: '1rem' }}>
                    <label style={{ fontSize: '0.8rem', display: 'block', marginBottom: '0.35rem' }}>Or Describe Amendment in Text:</label>
                    <textarea 
                      className="chat-input"
                      style={{ width: '100%', height: '110px' }}
                      placeholder="e.g. Effective Date 2026-12-01. Version 5.1. Increase Spot PO threshold to INR 300,000. Increase Emergency PO limit to 750,000 INR..."
                      value={amendmentText}
                      onChange={(e) => setAmendmentText(e.target.value)}
                    />
                  </div>

                  <button 
                    className="btn btn-primary" 
                    onClick={handlePreviewAmendment}
                    disabled={policyLoading || (!amendmentFile && !amendmentText.trim())}
                  >
                    Preview Plain-English Diff
                  </button>
                </div>

                {/* Diff Preview Pane */}
                <div>
                  <h4 style={{ marginBottom: '0.75rem' }}>Diff & Impact Preview</h4>
                  {amendmentDiff ? (
                    <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-md)', padding: '1rem' }}>
                      <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '0.5rem' }}>
                        Proposed Version: {amendmentDiff.new_version} (from {amendmentDiff.base_version})
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                        Effective Date: {amendmentDiff.effective_date}
                      </div>

                      <div style={{ marginBottom: '1rem' }}>
                        <strong>Detected Rule Modifications:</strong>
                        <ul style={{ fontSize: '0.85rem', marginTop: '0.5rem', paddingLeft: '1.25rem', color: '#34d399' }}>
                          {amendmentDiff.summary_of_changes.map((c: string, idx: number) => (
                            <li key={idx}>{c}</li>
                          ))}
                        </ul>
                      </div>

                      <button 
                        className="btn btn-success" 
                        style={{ width: '100%' }}
                        onClick={() => handleApproveAmendment(amendmentDiff.new_version)}
                        disabled={policyLoading}
                      >
                        <CheckCircle2 size={16} /> Approve & Activate Version {amendmentDiff.new_version}
                      </button>
                    </div>
                  ) : (
                    <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-dim)', background: 'rgba(255,255,255,0.02)', borderRadius: 'var(--radius-md)' }}>
                      Upload or enter an amendment on the left to review the policy diff before activation.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 5. PREFERRED SUPPLIERS TAB */}
        {activeTab === 'suppliers' && (
          <div>
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <Award size={20} color="var(--accent-amber)" /> Preferred Supplier Directory (Policy Section 6)
                </div>
                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                  <input 
                    type="date" 
                    className="chat-input"
                    value={prefDate}
                    onChange={(e) => {
                      setPrefDate(e.target.value);
                      fetchPreferredSuppliers(e.target.value);
                    }}
                  />
                  <a href={`/api/suppliers/preferred/export?date=${prefDate}`} download className="btn btn-success btn-sm">
                    <Download size={14} /> Export CSV
                  </a>
                </div>
              </div>

              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Item Code</th>
                      <th>Rank</th>
                      <th>Supplier ID</th>
                      <th>Supplier Name</th>
                      <th>Reference Price</th>
                      <th>Composite Score</th>
                      <th>POs (548d)</th>
                      <th>Recency</th>
                      <th>Contract</th>
                      <th>On-Time %</th>
                      <th>Quality</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(preferredItems).slice(0, 40).map(([itemCode, rankedList]: any) => (
                      rankedList.map((supp: any, idx: number) => (
                        <tr key={`${itemCode}-${supp.supplier_id}`}>
                          {idx === 0 ? (
                            <td rowSpan={rankedList.length} style={{ verticalAlign: 'top', borderRight: '1px solid var(--border-color)', fontWeight: 700 }}>
                              <code>{itemCode}</code>
                            </td>
                          ) : null}
                          <td><span className="badge badge-emerald">#{supp.rank}</span></td>
                          <td><code>{supp.supplier_id}</code></td>
                          <td><strong>{supp.supplier_name}</strong></td>
                          <td style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>₹{supp.reference_price}</td>
                          <td><strong style={{ color: '#fff' }}>{supp.composite_score}</strong></td>
                          <td>{supp.po_count_548d}</td>
                          <td>{supp.recency_score}</td>
                          <td>{supp.has_contract ? <span style={{ color: '#34d399' }}>Yes</span> : 'No'}</td>
                          <td>{supp.on_time_pct}%</td>
                          <td>{supp.quality_rating} / 5.0</td>
                        </tr>
                      ))
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* 6. CONTRACTS REGISTER TAB */}
        {activeTab === 'contracts' && (
          <div>
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <FileText size={20} color="var(--accent-cyan)" /> Active Rate Contracts & Ceilings
                </div>
                <span className="badge badge-blue">{contractsList.length} Loaded Contracts</span>
              </div>

              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Contract ID</th>
                      <th>Supplier</th>
                      <th>Validity</th>
                      <th>Ceiling Cap</th>
                      <th>Consumed</th>
                      <th>Remaining Headroom</th>
                      <th>Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {contractsList.map((c, i) => {
                      const pct = Math.min(100, Math.round((c.consumed_value / c.value_cap) * 100));
                      const remaining = Math.max(0, c.value_cap - c.consumed_value);
                      return (
                        <tr key={i}>
                          <td><code>{c.contract_id}</code></td>
                          <td>{c.supplier_name} ({c.supplier_id})</td>
                          <td style={{ fontSize: '0.8rem' }}>{c.start_date} → {c.end_date}</td>
                          <td>₹{c.value_cap.toLocaleString()}</td>
                          <td>₹{c.consumed_value.toLocaleString()} ({pct}%)</td>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <div style={{ width: '80px', height: '6px', background: 'var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
                                <div style={{ width: `${pct}%`, height: '100%', background: pct > 90 ? 'var(--accent-rose)' : 'var(--accent-cyan)' }} />
                              </div>
                              <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>₹{remaining.toLocaleString()}</span>
                            </div>
                          </td>
                          <td>
                            {c.is_pdf_extracted ? (
                              <span className="badge badge-purple">PDF Extracted</span>
                            ) : (
                              <span className="badge badge-dim">CSV Register</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
