import React from 'react';
import { Activity, Droplet } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Cell } from 'recharts';

const Dashboard = ({ reportData }) => {
    if (!reportData) return null;

    const getBarColor = (val) => {
        if (val < 90) return "#ef4444"; // אדום מודרני
        if (val > 110) return "#3b82f6"; // כחול מודרני
        return "#10b981"; // ירוק מודרני
    };

    const topNutrients = reportData.report
        ? [...reportData.report]
            .sort((a, b) => b.percentage - a.percentage)
            .slice(0, 4)
        : [];

    return (
        <div className="dashboard-grid">
            {/* צד שמאל: סיכום טקסטואלי + מדדים */}
            <section className="card">
                <h3><Activity size={20} color="#2563eb" /> AI Assessment</h3>
                <div className="summary-content">
                    {reportData.summary}
                </div>

                <div className="metrics-container">
                    {topNutrients.length > 0 ? (
                        topNutrients.map((item, idx) => (
                            <div className="metric-item" key={idx}>
                                <span className="metric-label" style={{ textTransform: 'capitalize' }}>
                                    {item.nutrient_name.replace(/_/g, ' ')}
                                </span>
                                <span className="metric-val" style={{ color: getBarColor(item.percentage) }}>
                                    {Math.round(item.percentage)}%
                                </span>
                            </div>
                        ))
                    ) : (
                        <p style={{ color: '#64748b', fontSize: '0.9rem', textAlign: 'center' }}>
                            No nutrient data available for this meal.
                        </p>
                    )}
                </div>
            </section>

            {/* צד ימין: גרף */}
            <section className="card">
                <h3><Droplet size={20} color="#2563eb" /> Micronutrient Status</h3>
                <div style={{ height: 350, width: '100%' }}>
                    <ResponsiveContainer>
                        <BarChart data={reportData.report} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                            <XAxis
                                dataKey="nutrient_name"
                                angle={-45}
                                textAnchor="end"
                                height={80}
                                interval={0}
                                tick={{ fill: '#6b7280', fontSize: 12 }}
                            />
                            <YAxis tick={{ fill: '#6b7280', fontSize: 12 }} />
                            <Tooltip
                                cursor={{ fill: '#f3f4f6' }}
                                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                            />
                            <ReferenceLine y={100} stroke="#9ca3af" strokeDasharray="3 3" />
                            <Bar dataKey="percentage" radius={[4, 4, 0, 0]}>
                                {reportData.report.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={getBarColor(entry.percentage)} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </section>
        </div>
    );
};

export default Dashboard;
