import React from 'react';
import { Utensils } from 'lucide-react';

const Recommendations = ({ recommendations }) => {
    if (!recommendations || recommendations.length === 0) return null;

    return (
        <section>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '20px', color: '#111827', display: 'flex', alignItems: 'center', gap: 10 }}>
                <Utensils size={24} color="#2563eb" />
                Smart Optimization
            </h3>
            <div className="rec-grid">
                {recommendations.map((rec, idx) => (
                    <div key={idx} className="rec-card">
                        <h4>{rec.food_name}</h4>
                        <div className="rec-meta">
                            <span>📏 {rec.serving}</span>
                            <span>🔥 {rec.calories} kcal</span>
                        </div>
                        <div className="rec-why">
                            {rec.reason}
                        </div>
                        <div className="tags">
                            {rec.tags.split(',').slice(0, 3).map(t => <span key={t}>{t}</span>)}
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
};

export default Recommendations;
