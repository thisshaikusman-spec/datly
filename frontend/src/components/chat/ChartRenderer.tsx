import { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, ScatterChart, Scatter, CartesianGrid,
  PieChart, Pie, Cell, Legend, AreaChart, Area
} from 'recharts';
import { Table as TableIcon, BarChart3 } from 'lucide-react';
import type { VisualizationSpec } from '../../services/api';

const CHART_COLORS = [
  '#a78bfa', '#f97316', '#34d399', '#60a5fa', '#f472b6',
  '#facc15', '#fb923c', '#818cf8', '#4ade80', '#e879f9'
];

interface ChartRendererProps {
  spec?: VisualizationSpec;
  specs?: VisualizationSpec[];
}

export function ChartRenderer({ spec, specs }: ChartRendererProps) {
  const chartSpecs = specs && specs.length > 0 ? specs : (spec ? [spec] : []);
  if (chartSpecs.length === 0) return null;

  return (
    <div className="flex flex-col gap-4 w-full">
      {chartSpecs.map((s, idx) => (
        <SingleChartRenderer key={`${s.type}-${s.title || idx}`} spec={s} />
      ))}
    </div>
  );
}

function SingleChartRenderer({ spec }: { spec: VisualizationSpec }) {
  const [showTable, setShowTable] = useState(false);

  // Cap data to 500 points for performance and clarity
  const originalLength = spec.data?.length ?? 0;
  const isCapped = originalLength > 500;
  const cappedData = isCapped ? spec.data!.slice(0, 500) : spec.data;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#1a1a1a] border border-white/10 p-3 rounded-lg shadow-xl">
          <p className="text-white/60 text-xs mb-1 uppercase tracking-wider">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-white text-sm font-mono">
              <span className="text-[#a78bfa] mr-2">{entry.name}:</span>
              {typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const renderHeader = (title?: string) => (
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        <h4 className="text-white/70 text-xs uppercase tracking-wider font-semibold">
          {title || (spec.type.toUpperCase() + ' CHART')}
        </h4>
        {isCapped && (
          <span className="text-[10px] bg-yellow-500/15 text-yellow-300 border border-yellow-500/30 px-1.5 py-0.5 rounded">
            Showing 500 of {originalLength} points
          </span>
        )}
      </div>
      {spec.data && spec.data.length > 0 && spec.type !== 'table' && spec.type !== 'kpi' && (
        <button
          onClick={() => setShowTable(!showTable)}
          className="flex items-center gap-1 text-[11px] text-white/50 hover:text-white/90 bg-white/5 hover:bg-white/10 px-2 py-1 rounded transition-colors"
          title={showTable ? 'Switch to chart' : 'Switch to table view'}
        >
          {showTable ? (
            <>
              <BarChart3 size={12} />
              <span>Chart</span>
            </>
          ) : (
            <>
              <TableIcon size={12} />
              <span>Table</span>
            </>
          )}
        </button>
      )}
    </div>
  );

  // If table fallback is toggled
  if (showTable && spec.data && spec.data.length > 0) {
    const columns = Object.keys(spec.data[0]);
    return (
      <div className="w-full mt-2 bg-white/[0.02] border border-white/5 rounded-xl p-4">
        {renderHeader(spec.title)}
        <div className="overflow-x-auto max-h-72">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-white/[0.02] border-b border-white/5 sticky top-0">
              <tr>
                {columns.map(col => (
                  <th key={col} className="px-4 py-2 font-medium text-white/60 capitalize text-xs">
                    {col.replace(/_/g, ' ')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {cappedData?.map((row: any, i: number) => (
                <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                  {columns.map(col => (
                    <td key={col} className="px-4 py-1.5 text-white/80 font-mono text-xs">
                      {typeof row[col] === 'number' ? row[col].toLocaleString() : row[col]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  switch (spec.type) {
    case 'bar': {
      if (!cappedData || cappedData.length === 0) return null;
      return (
        <div className="h-72 w-full mt-2 bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col">
          {renderHeader(spec.title)}
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={cappedData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                <XAxis
                  dataKey={spec.x}
                  stroke="#ffffff40"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#ffffff60' }}
                />
                <YAxis
                  stroke="#ffffff40"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#ffffff60' }}
                  tickFormatter={(value) => value >= 1000000 ? `${(value / 1000000).toFixed(1)}M` : value >= 1000 ? `${(value / 1000).toFixed(1)}K` : value}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: '#ffffff05' }} />
                <Bar dataKey={spec.y || ''} fill="#a78bfa" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      );
    }

    case 'line': {
      if (!cappedData || cappedData.length === 0) return null;
      return (
        <div className="h-72 w-full mt-2 bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col">
          {renderHeader(spec.title)}
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={cappedData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                <XAxis
                  dataKey={spec.x}
                  stroke="#ffffff40"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#ffffff60' }}
                />
                <YAxis
                  stroke="#ffffff40"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#ffffff60' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey={spec.y || ''}
                  stroke="#a78bfa"
                  strokeWidth={2}
                  dot={{ fill: '#a78bfa', strokeWidth: 0, r: 4 }}
                  activeDot={{ r: 6, fill: '#fff' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      );
    }

    case 'pie': {
      let pieData: { name: string; value: number }[] = [];

      if (spec.labels && spec.values && spec.labels.length > 0) {
        pieData = spec.labels.map((label, i) => ({
          name: label,
          value: spec.values![i] ?? 0
        }));
      } else if (cappedData && cappedData.length > 0 && spec.x && spec.y) {
        pieData = cappedData.map((row: any) => ({
          name: String(row[spec.x!] ?? ''),
          value: Number(row[spec.y!] ?? 0)
        }));
      }

      if (pieData.length === 0) return null;

      const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
        if (percent < 0.05) return null;
        const RADIAN = Math.PI / 180;
        const radius = innerRadius + (outerRadius - innerRadius) * 0.6;
        const x = cx + radius * Math.cos(-midAngle * RADIAN);
        const y = cy + radius * Math.sin(-midAngle * RADIAN);
        return (
          <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={11}>
            {`${(percent * 100).toFixed(1)}%`}
          </text>
        );
      };

      return (
        <div className="w-full mt-2 bg-white/[0.02] border border-white/5 rounded-xl p-4">
          {renderHeader(spec.title)}
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={100}
                dataKey="value"
                labelLine={false}
                label={renderCustomLabel}
              >
                {pieData.map((_: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: any, name: any) => [
                  typeof value === 'number' ? value.toLocaleString() : value,
                  name
                ]}
                contentStyle={{ background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                labelStyle={{ color: 'rgba(255,255,255,0.6)', fontSize: 11 }}
                itemStyle={{ color: '#fff', fontSize: 12 }}
              />
              <Legend
                formatter={(value) => <span style={{ color: 'rgba(255,255,255,0.7)', fontSize: 11 }}>{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      );
    }

    case 'kpi': {
      const data = spec.data as any[];
      if (!data || data.length === 0) return null;
      const kpiValue = data[0] && 'value' in data[0]
        ? data[0].value
        : (data[0] ? Object.values(data[0])[0] : null);

      return (
        <div className="mt-2 bg-white/[0.02] border border-white/5 rounded-xl p-6 flex flex-col items-center justify-center text-center">
          <h4 className="text-white/60 text-xs uppercase tracking-wider mb-2 font-semibold">{spec.title || 'Summary KPI'}</h4>
          <p className="text-3xl font-light text-white tracking-tight">
            {typeof kpiValue === 'number'
              ? kpiValue.toLocaleString()
              : kpiValue}
          </p>
        </div>
      );
    }

    case 'histogram': {
      let histData: { range: string; count: number }[] = [];

      if (spec.bins && spec.frequencies && spec.bins.length > 0) {
        histData = spec.bins.map((bin, i) => ({
          range: bin.toLocaleString(undefined, { maximumFractionDigits: 1 }),
          count: spec.frequencies![i] ?? 0
        }));
      } else if (cappedData && cappedData.length > 0 && spec.x) {
        const vals = cappedData
          .map((r: any) => Number(r[spec.x!]))
          .filter((v: number) => !isNaN(v));
        if (vals.length > 0) {
          const min = Math.min(...vals);
          const max = Math.max(...vals);
          const binCount = Math.min(15, Math.max(5, Math.round(vals.length ** 0.5)));
          const width = (max - min) / binCount || 1;
          const buckets = Array.from({ length: binCount }, (_, i) => ({
            range: (min + i * width).toLocaleString(undefined, { maximumFractionDigits: 1 }),
            count: 0
          }));
          vals.forEach((v: number) => {
            const idx = Math.min(Math.floor((v - min) / width), binCount - 1);
            buckets[idx].count++;
          });
          histData = buckets;
        }
      }

      if (histData.length === 0) return null;

      return (
        <div className="h-72 w-full mt-2 bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col">
          {renderHeader(spec.title)}
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={histData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }} barCategoryGap="2%">
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                <XAxis
                  dataKey="range"
                  stroke="#ffffff40"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#ffffff60' }}
                />
                <YAxis
                  stroke="#ffffff40"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#ffffff60' }}
                  label={{ value: 'Frequency', angle: -90, position: 'insideLeft', fill: '#ffffff40', fontSize: 10 }}
                />
                <Tooltip
                  formatter={(value: any) => [value, 'Frequency']}
                  contentStyle={{ background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  labelStyle={{ color: 'rgba(255,255,255,0.6)', fontSize: 11 }}
                  itemStyle={{ color: '#fff' }}
                />
                <Bar dataKey="count" fill="#a78bfa" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      );
    }

    case 'scatter': {
      if (!cappedData || cappedData.length === 0) return null;
      return (
        <div className="h-72 w-full mt-2 bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col">
          {renderHeader(spec.title)}
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                <XAxis type="number" dataKey={spec.x} name={spec.x} stroke="#ffffff40" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis type="number" dataKey={spec.y} name={spec.y} stroke="#ffffff40" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />
                <Scatter name={spec.title} data={cappedData} fill="#a78bfa" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      );
    }

    case 'area': {
      if (!cappedData || cappedData.length === 0) return null;
      return (
        <div className="h-72 w-full mt-2 bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col">
          {renderHeader(spec.title)}
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={cappedData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#a78bfa" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#a78bfa" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                <XAxis
                  dataKey={spec.x}
                  stroke="#ffffff40"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#ffffff60' }}
                />
                <YAxis
                  stroke="#ffffff40"
                  fontSize={11}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: '#ffffff60' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey={spec.y || ''}
                  stroke="#a78bfa"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#areaGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      );
    }

    case 'box': {
      let stats = spec.stats;
      const col = spec.y || spec.x;
      if (!stats && cappedData && cappedData.length > 0 && col) {
        const nums = cappedData
          .map((r: any) => Number(r[col]))
          .filter((v: number) => !isNaN(v))
          .sort((a: number, b: number) => a - b);
        if (nums.length > 0) {
          const q = (p: number) => {
            const pos = (nums.length - 1) * p;
            const base = Math.floor(pos);
            const rest = pos - base;
            return nums[base + 1] !== undefined ? nums[base] + rest * (nums[base + 1] - nums[base]) : nums[base];
          };
          stats = {
            min: nums[0],
            q1: q(0.25),
            median: q(0.5),
            q3: q(0.75),
            max: nums[nums.length - 1]
          };
        }
      }
      if (!stats) return null;
      return (
        <div className="w-full mt-2 bg-white/[0.02] border border-white/5 rounded-xl p-5">
          {renderHeader(spec.title || 'Distribution (Box Plot)')}
          <div className="grid grid-cols-5 gap-2 text-center mb-4">
            <div className="bg-white/[0.03] p-2 rounded-lg border border-white/5">
              <span className="text-white/40 text-[10px] block uppercase font-mono">Min</span>
              <span className="text-white font-mono text-sm font-semibold">{stats.min.toLocaleString()}</span>
            </div>
            <div className="bg-white/[0.03] p-2 rounded-lg border border-white/5">
              <span className="text-white/40 text-[10px] block uppercase font-mono">Q1 (25%)</span>
              <span className="text-white font-mono text-sm font-semibold">{stats.q1.toLocaleString()}</span>
            </div>
            <div className="bg-[#a78bfa]/15 p-2 rounded-lg border border-[#a78bfa]/30">
              <span className="text-[#a78bfa] text-[10px] block uppercase font-mono font-bold">Median</span>
              <span className="text-white font-mono text-sm font-bold">{stats.median.toLocaleString()}</span>
            </div>
            <div className="bg-white/[0.03] p-2 rounded-lg border border-white/5">
              <span className="text-white/40 text-[10px] block uppercase font-mono">Q3 (75%)</span>
              <span className="text-white font-mono text-sm font-semibold">{stats.q3.toLocaleString()}</span>
            </div>
            <div className="bg-white/[0.03] p-2 rounded-lg border border-white/5">
              <span className="text-white/40 text-[10px] block uppercase font-mono">Max</span>
              <span className="text-white font-mono text-sm font-semibold">{stats.max.toLocaleString()}</span>
            </div>
          </div>
          <div className="relative w-full h-8 flex items-center px-4">
            <div className="w-full h-1 bg-white/10 rounded relative">
              {stats.max > stats.min && (
                <>
                  <div
                    className="absolute h-5 bg-[#a78bfa]/30 border border-[#a78bfa] rounded -top-2"
                    style={{
                      left: `${((stats.q1 - stats.min) / (stats.max - stats.min)) * 100}%`,
                      width: `${Math.max(2, ((stats.q3 - stats.q1) / (stats.max - stats.min)) * 100)}%`
                    }}
                  />
                  <div
                    className="absolute w-0.5 h-6 bg-white -top-2.5 z-10"
                    style={{
                      left: `${((stats.median - stats.min) / (stats.max - stats.min)) * 100}%`
                    }}
                  />
                </>
              )}
            </div>
          </div>
        </div>
      );
    }

    case 'table': {
      if (!cappedData || cappedData.length === 0) return null;
      const columns = Object.keys(cappedData[0]);
      return (
        <div className="w-full mt-2 bg-white/[0.02] border border-white/5 rounded-xl overflow-hidden p-4">
          {renderHeader(spec.title)}
          <div className="overflow-x-auto max-h-72">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-white/[0.02] border-b border-white/5 sticky top-0">
                <tr>
                  {columns.map(col => (
                    <th key={col} className="px-4 py-2 font-medium text-white/60 capitalize text-xs">
                      {col.replace(/_/g, ' ')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {cappedData.map((row: any, i: number) => (
                  <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                    {columns.map(col => (
                      <td key={col} className="px-4 py-1.5 text-white/80 font-mono text-xs">
                        {typeof row[col] === 'number' ? row[col].toLocaleString() : row[col]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    case 'none':
      return null;

    default: {
      const unknownType = (spec as any).type;
      if (!unknownType || unknownType === 'none') return null;
      return (
        <div className="mt-2 bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-4 text-yellow-400 text-xs">
          ⚠️ Unsupported chart type: <code className="font-mono">{unknownType}</code>
        </div>
      );
    }
  }
}
