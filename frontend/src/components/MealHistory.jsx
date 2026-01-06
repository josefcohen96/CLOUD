import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { X, FileText, Calendar } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

// כתובת ה-API שלך
const API_URL = "https://ldclmiawsh.execute-api.us-east-1.amazonaws.com/default";

const MealDetails = ({ meal, onClose, userId }) => {
  const [mealReport, setMealReport] = useState([]);
  const [loadingReport, setLoadingReport] = useState(false);
  let analysisContent = null;

  // שליפת נתוני גרף עבור הארוחה הספציפית
  useEffect(() => {
    if (meal?.meal_id && userId) {
      setLoadingReport(true);
      axios.get(`${API_URL}/report/${userId}?meal_id=${meal.meal_id}`)
        .then(res => {
          setMealReport(res.data.report || []);
        })
        .catch(err => {
          console.error("Error fetching meal report:", err);
          setMealReport([]);
        })
        .finally(() => setLoadingReport(false));
    }
  }, [meal?.meal_id, userId]);

  try {
    const parsedData = typeof meal.ai_analysis_summary === 'string'
      ? JSON.parse(meal.ai_analysis_summary)
      : meal.ai_analysis_summary;

    if (parsedData && parsedData.text) {
      analysisContent = (
        <div style={styles.analysisText}>
          {parsedData.text.split('\n').map((paragraph, index) => (
            <p key={index} style={styles.paragraph}>{paragraph}</p>
          ))}
        </div>
      );
    } else {
      analysisContent = (
        <pre style={styles.jsonPre}>
          {JSON.stringify(parsedData, null, 2)}
        </pre>
      );
    }
  } catch (e) {
    analysisContent = <p style={styles.paragraph}>{meal.ai_analysis_summary}</p>;
  }

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <h3 style={styles.modalTitle}>
            <FileText size={24} style={{ marginRight: '10px', color: '#2563eb' }} />
            דוח ארוחה מפורט
          </h3>
          <button onClick={onClose} style={styles.closeIconButton}>
            <X size={24} />
          </button>
        </div>

        <div style={styles.modalBody}>
          <div style={styles.mealMeta}>
            <Calendar size={16} style={{ marginRight: '5px' }} />
            <strong>תאריך:</strong> {new Date(meal.created_at).toLocaleDateString('he-IL')}
            <span style={{ margin: '0 10px' }}>|</span>
            <strong>שעה:</strong> {new Date(meal.created_at).toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })}
          </div>

          {/* הצגת תמונת הארוחה מה-S3 */}
          {meal.image_url && (
            <div style={styles.imageContainer}>
              <img src={meal.image_url} alt="Meal" style={styles.mealImage} />
            </div>
          )}

          {/* גרף תרומה תזונתית של הארוחה */}
          <div style={styles.chartSection}>
            <h4 style={styles.sectionTitle}>תרומה תזונתית לארוחה זו (%)</h4>
            <div style={{ height: 180, width: '100%' }}>
              <ResponsiveContainer>
                <BarChart data={mealReport}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="nutrient_name" hide />
                  <YAxis fontSize={10} tick={{ fill: '#64748b' }} />
                  <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }} />
                  <Bar dataKey="percentage" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                    {mealReport.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.percentage > 50 ? '#10b981' : '#3b82f6'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div style={styles.scrollableContent}>
            <h4 style={styles.sectionTitle}>ניתוח AI קליני</h4>
            {analysisContent}
          </div>
        </div>
      </div>
    </div>
  );
};

export default function MealHistory({ userId }) {
  const [meals, setMeals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedMeal, setSelectedMeal] = useState(null);

  useEffect(() => {
    if (userId) fetchHistory();
  }, [userId]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_URL}/history/${userId}`);
      setMeals(response.data);
    } catch (error) {
      console.error("Error fetching history:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div style={styles.loading}>טוען היסטוריה...</div>;
  if (meals.length === 0) return <div style={styles.emptyState}>אין עדיין ארוחות שמורות.</div>;

  return (
    <div style={styles.container}>
      <h2 style={styles.historyTitle}>הארוחות שלי</h2>
      <div style={styles.grid}>
        {meals.map((meal) => (
          <div key={meal.meal_id} style={styles.card} onClick={() => setSelectedMeal(meal)}>
            <div style={styles.cardHeader}>
              <span style={{ fontSize: '1.2rem' }}>📅</span> {new Date(meal.created_at).toLocaleDateString('he-IL', { day: 'numeric', month: 'numeric' })}
            </div>
            <div style={styles.cardBody}>
              <span style={{ fontSize: '1.1rem' }}>🕒</span> {new Date(meal.created_at).toLocaleTimeString('he-IL', { hour: '2-digit', minute: '2-digit' })}
            </div>
            <div style={styles.cardFooter}>
              לחץ לפרטים
            </div>
          </div>
        ))}
      </div>

      {selectedMeal && (
        <MealDetails
          meal={selectedMeal}
          userId={userId}
          onClose={() => setSelectedMeal(null)}
        />
      )}
    </div>
  );
}

// --- סגנונות מורחבים ---
const styles = {
  // ... סגנונות קודמים שהיו לך ...
  container: { marginTop: '25px', padding: '15px', backgroundColor: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' },
  historyTitle: { fontSize: '1.25rem', fontWeight: '600', color: '#1e293b', marginBottom: '15px', textAlign: 'center' },
  loading: { padding: '20px', textAlign: 'center', color: '#64748b' },
  emptyState: { padding: '20px', textAlign: 'center', color: '#64748b', fontStyle: 'italic' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))', gap: '12px' },
  card: { backgroundColor: '#fff', borderRadius: '10px', padding: '12px', cursor: 'pointer', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', textAlign: 'center', border: '1px solid #f1f5f9' },
  cardHeader: { fontWeight: '600', fontSize: '0.95rem', color: '#334155', marginBottom: '4px' },
  cardBody: { fontSize: '0.9rem', color: '#64748b', marginBottom: '8px' },
  cardFooter: { fontSize: '0.75rem', color: '#2563eb', fontWeight: '500' },

  modalOverlay: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1050, padding: '20px' },
  modalContent: { backgroundColor: '#fff', borderRadius: '16px', width: '100%', maxWidth: '650px', maxHeight: '90vh', display: 'flex', flexDirection: 'column', boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)', overflow: 'hidden', direction: 'rtl' },
  modalHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 24px', borderBottom: '1px solid #e2e8f0', backgroundColor: '#f8fafc' },
  modalTitle: { margin: 0, fontSize: '1.4rem', fontWeight: '700', color: '#1e293b', display: 'flex', alignItems: 'center' },
  closeIconButton: { background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer', padding: '8px' },
  modalBody: { padding: '24px', overflowY: 'auto', flexGrow: 1 },
  mealMeta: { display: 'flex', alignItems: 'center', fontSize: '0.9rem', color: '#64748b', marginBottom: '15px', paddingBottom: '10px', borderBottom: '1px dashed #e2e8f0' },

  // סגנונות חדשים לתמונה ולגרף
  imageContainer: { width: '100%', borderRadius: '12px', overflow: 'hidden', marginBottom: '20px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' },
  mealImage: { width: '100%', maxHeight: '250px', objectFit: 'cover' },
  chartSection: { backgroundColor: '#f1f5f9', padding: '15px', borderRadius: '12px', marginBottom: '20px' },
  sectionTitle: { fontSize: '1rem', fontWeight: '600', color: '#334155', marginBottom: '12px', textAlign: 'right' },

  analysisText: { lineHeight: '1.7', color: '#334155', fontSize: '1.05rem' },
  paragraph: { marginBottom: '16px', textAlign: 'right' },
  jsonPre: { whiteSpace: 'pre-wrap', textAlign: 'left', direction: 'ltr', backgroundColor: '#f1f5f9', padding: '16px', borderRadius: '8px', fontSize: '0.9rem' }
};