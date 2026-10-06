import { Database, Sparkles, BarChart2, TrendingUp, Users, Activity } from 'lucide-react';

export function ProductPreview() {
  return (
    <div className="w-full max-w-6xl mx-auto px-4 md:px-8 pb-32 z-10 relative">
      <div className="flex items-center justify-center gap-4 mb-8 text-white/30 text-xs font-mono tracking-widest uppercase">
        <div className="w-12 h-[1px] bg-white/10"></div>
        Datly Workspace
        <div className="w-12 h-[1px] bg-white/10"></div>
      </div>
      
      <div className="bg-[#1a1a1a]/80 backdrop-blur-xl border border-white/10 rounded-2xl p-2 shadow-[0_30px_60px_-15px_rgba(0,0,0,0.5)] overflow-hidden ring-1 ring-white/5">
        <div className="bg-[#121212] rounded-xl border border-white/5 flex flex-col md:flex-row h-auto md:h-[600px] overflow-hidden relative">
          
          <div className="absolute top-0 right-0 w-96 h-96 bg-[#8b5cf6]/5 rounded-full blur-[100px] pointer-events-none"></div>
          
          <div className="w-full md:w-64 border-b md:border-b-0 md:border-r border-white/5 p-4 md:p-5 bg-white/[0.01] flex flex-col gap-8 shrink-0 z-10">
            <div>
              <div className="text-[10px] text-white/40 uppercase font-semibold tracking-widest mb-3 px-1">Dataset</div>
              <div className="flex items-center gap-3 bg-white/5 p-3 rounded-lg border border-white/5 transition-colors hover:bg-white/10 cursor-pointer">
                <Database size={16} className="text-[#3b82f6]" />
                <div className="overflow-hidden">
                  <div className="text-sm font-medium text-white/90 truncate">Q3_Revenue_Data.csv</div>
                  <div className="text-xs text-white/40 mt-0.5">24,592 rows • 18 cols</div>
                </div>
              </div>
            </div>
            
            <div>
              <div className="text-[10px] text-white/40 uppercase font-semibold tracking-widest mb-3 px-1">Suggested Queries</div>
              <div className="flex flex-col gap-1.5">
                {['What was the top selling product in Q3?', 'Show revenue by region', 'Compare user growth YoY'].map((q, i) => (
                  <div key={i} className="text-xs text-white/60 hover:text-white/90 hover:bg-white/5 p-2 rounded-md cursor-pointer transition-colors border border-transparent hover:border-white/5 truncate">
                    {q}
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          <div className="flex-1 p-4 md:p-6 flex flex-col gap-4 md:gap-6 overflow-hidden z-10">
            
            <div className="bg-white/[0.03] rounded-xl p-4 md:p-5 border border-white/10 flex flex-col gap-4 shadow-sm">
              <div className="flex items-start gap-3 md:gap-4">
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#8b5cf6] to-[#ec4899] flex items-center justify-center shrink-0 mt-0.5 shadow-inner">
                  <Sparkles size={14} className="text-white" />
                </div>
                <div>
                  <div className="text-sm md:text-base text-white/90 font-medium mb-1.5">Show me the revenue breakdown by region for the top 3 products.</div>
                  <div className="text-[11px] text-white/40 flex items-center gap-2 font-mono">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                    Analyzed 24,592 rows in 1.2s
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
              {[
                { label: 'Total Revenue', value: '$2.4M', trend: '+14.5%', icon: TrendingUp, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
                { label: 'Active Users', value: '45.2K', trend: '+8.2%', icon: Users, color: 'text-blue-400', bg: 'bg-blue-400/10' },
                { label: 'Avg Order Value', value: '$184', trend: '-2.1%', icon: Activity, color: 'text-rose-400', bg: 'bg-rose-400/10' },
                { label: 'Conversion Rate', value: '3.8%', trend: '+0.4%', icon: BarChart2, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
              ].map((kpi, i) => (
                <div key={i} className="bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col gap-3 hover:bg-white/[0.03] transition-colors">
                  <div className="text-[11px] text-white/40 flex items-center justify-between font-medium uppercase tracking-wider">
                    {kpi.label}
                    <kpi.icon size={14} className="text-white/20" />
                  </div>
                  <div className="text-2xl md:text-3xl font-semibold text-white/90 tracking-tight">{kpi.value}</div>
                  <div className={`text-[11px] font-medium flex items-center gap-1.5`}>
                    <span className={`px-1.5 py-0.5 rounded ${kpi.bg} ${kpi.color}`}>{kpi.trend}</span>
                    <span className="text-white/30">vs last quarter</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex-1 bg-white/[0.02] border border-white/5 rounded-xl p-5 flex flex-col min-h-[250px]">
              <div className="text-sm font-medium text-white/80 mb-6">Revenue by Region (Top 3 Products)</div>
              <div className="flex-1 flex items-end gap-2 md:gap-6 justify-between px-2 md:px-8 pb-6 border-b border-white/5 relative mt-4">
                
                <div className="absolute inset-0 flex flex-col justify-between pointer-events-none pb-6">
                  {[0, 1, 2, 3, 4].map(i => (
                    <div key={i} className="w-full border-t border-white/[0.03] h-[1px]"></div>
                  ))}
                </div>

                {[
                  { region: 'NA', p1: 85, p2: 65, p3: 45 },
                  { region: 'EMEA', p1: 60, p2: 75, p3: 30 },
                  { region: 'APAC', p1: 95, p2: 40, p3: 55 },
                  { region: 'LATAM', p1: 35, p2: 25, p3: 15 },
                ].map((item, i) => (
                  <div key={i} className="flex flex-col items-center gap-4 z-10 w-full group cursor-pointer">
                    <div className="flex items-end gap-1 md:gap-1.5 w-full justify-center h-32 md:h-40 relative">
                      <div className="absolute -top-10 bg-[#2a2a2a] text-white text-[10px] px-2 py-1 rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity border border-white/10 pointer-events-none whitespace-nowrap">
                        {item.region} Data
                      </div>
                      <div className="w-1/3 md:w-8 bg-[#3b82f6] rounded-t opacity-80 group-hover:opacity-100 transition-all duration-300" style={{ height: `${item.p1}%` }}></div>
                      <div className="w-1/3 md:w-8 bg-[#8b5cf6] rounded-t opacity-80 group-hover:opacity-100 transition-all duration-300 delay-75" style={{ height: `${item.p2}%` }}></div>
                      <div className="w-1/3 md:w-8 bg-[#ec4899] rounded-t opacity-80 group-hover:opacity-100 transition-all duration-300 delay-150" style={{ height: `${item.p3}%` }}></div>
                    </div>
                    <div className="text-[11px] font-medium text-white/40 uppercase tracking-widest">{item.region}</div>
                  </div>
                ))}
              </div>
              <div className="flex items-center justify-center gap-6 mt-5">
                <div className="flex items-center gap-2 text-[11px] text-white/50"><div className="w-2.5 h-2.5 rounded-sm bg-[#3b82f6] opacity-80"></div>Product Alpha</div>
                <div className="flex items-center gap-2 text-[11px] text-white/50"><div className="w-2.5 h-2.5 rounded-sm bg-[#8b5cf6] opacity-80"></div>Product Beta</div>
                <div className="flex items-center gap-2 text-[11px] text-white/50"><div className="w-2.5 h-2.5 rounded-sm bg-[#ec4899] opacity-80"></div>Product Gamma</div>
              </div>
            </div>
            
          </div>
        </div>
      </div>
    </div>
  );
}
