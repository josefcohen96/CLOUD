import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { X, FileText, Calendar } from 'lucide-react'; // אייקונים חדשים

// קומפוננטה להצגת פרטי ארוחה אחת (Modal)
const MealDetails = ({ meal, onClose }) => {
  let analysisContent = null;
  
  try {
    // מנסים לפרסר את המידע. אם זה סטרינג, מפרסרים אותו ל-JSON.
    const parsedData = typeof meal.ai_analysis_summary === 'string' 
      ? JSON.parse(meal.ai_analysis_summary) 
      : meal.ai_analysis_summary;

    // אם המידע הוא אובייקט ויש לו שדה 'text', נציג את הטקסט הנקי
    if (parsedData && parsedData.text) {
      analysisContent = (
        <div style={styles.analysisText}>
          {parsedData.text.split('\n').map((paragraph, index) => (
            <p key={index} style={styles.paragraph}>{paragraph}</p>
          ))}
        </div>
      );
    } else {
      // fallback למקרה שהמבנה שונה, מציגים בצורה יפה של JSON
      analysisContent = (
        <pre style={styles.jsonPre}>
          {JSON.stringify(parsedData, null, 2)}
        </pre>
      );
    }
  } catch (e) {
    // במקרה של שגיאה בפרסור, מציגים את הטקסט הגולמי
    analysisContent = <p style={styles.paragraph}>{meal.ai_analysis_summary}</p>;
  }

  return (
    <div style={styles.modalOverlay} onClick={onClose}>
      <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
        <div style={styles.modalHeader}>
          <h3 style={styles.modalTitle}>
            <FileText size={24} style={{ marginRight: '10px', color: '#2563eb' }} />
            דוח ארוחה
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

          <div style={styles.scrollableContent}>
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
      // שים לב: הכתובת צריכה להיות תואמת ל-API שלך
      const response = await axios.get(`https://ldclmiawsh.execute-api.us-east-1.amazonaws.com/default/history/${userId}`);
      setMeals(response.data);
    } catch (error) {
      console.error("Error fetching history:", error);
      // alert("לא הצלחנו לטעון את ההיסטוריה"); // אפשר להעיר כדי לא להציק
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
                <span style={{ fontSize: '1.1rem' }}>🕒</span> {new Date(meal.created_at).toLocaleTimeString('he-IL', {hour: '2-digit', minute:'2-digit'})}
            </div>
             <div style={styles.cardFooter}>
                לחץ לפרטים
            </div>
          </div>
        ))}
      </div>

      {selectedMeal && (
        <MealDetails meal={selectedMeal} onClose={() => setSelectedMeal(null)} />
      )}
    </div>
  );
}

// --- סגנונות מעודכנים ---
const styles = {
  container: { 
    marginTop: '25px', 
    padding: '15px', 
    backgroundColor: '#f8fafc', 
    borderRadius: '12px',
    border: '1px solid #e2e8f0'
  },
  historyTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    color: '#1e293b',
    marginBottom: '15px',
    textAlign: 'center'
  },
  loading: { padding: '20px', textAlign: 'center', color: '#64748b' },
  emptyState: { padding: '20px', textAlign: 'center', color: '#64748b', fontStyle: 'italic' },
  grid: { 
    display: 'grid', 
    gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))', 
    gap: '12px' 
  },
  card: { 
    backgroundColor: '#fff',
    borderRadius: '10px', 
    padding: '12px', 
    cursor: 'pointer', 
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    transition: 'all 0.2s ease-in-out',
    border: '1px solid #f1f5f9',
    textAlign: 'center',
    ':hover': {
        transform: 'translateY(-2px)',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
    }
  },
  cardHeader: { 
    fontWeight: '600', 
    fontSize: '0.95rem',
    color: '#334155',
    marginBottom: '4px'
  },
  cardBody: {
    fontSize: '0.9rem',
    color: '#64748b',
    marginBottom: '8px'
  },
  cardFooter: {
      fontSize: '0.75rem',
      color: '#2563eb',
      fontWeight: '500'
  },

  // --- סגנונות המודל החדשים ---
  modalOverlay: {
    position: 'fixed', 
    top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: 'rgba(15, 23, 42, 0.6)', // רקע כהה ומודרני יותר
    backdropFilter: 'blur(4px)', // אפקט טשטוש לרקע
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    zIndex: 1050,
    padding: '20px'
  },
  modalContent: {
    backgroundColor: '#fff', 
    borderRadius: '16px',
    width: '100%', 
    maxWidth: '650px', 
    maxHeight: '85vh', 
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    overflow: 'hidden', // חשוב לגלילה פנימית
    direction: 'rtl' // תמיכה בעברית
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 24px',
    borderBottom: '1px solid #e2e8f0',
    backgroundColor: '#f8fafc'
  },
  modalTitle: {
    margin: 0,
    fontSize: '1.4rem',
    fontWeight: '700',
    color: '#1e293b',
    display: 'flex',
    alignItems: 'center'
  },
  closeIconButton: {
    background: 'transparent', 
    border: 'none', 
    color: '#64748b',
    cursor: 'pointer',
    padding: '8px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.2s',
    ':hover': {
        backgroundColor: '#e2e8f0',
        color: '#ef4444'
    }
  },
  modalBody: {
    padding: '24px',
    overflowY: 'auto', // גלילה רק לתוכן הגוף
    flexGrow: 1
  },
  mealMeta: {
      display: 'flex',
      alignItems: 'center',
      fontSize: '0.9rem',
      color: '#64748b',
      marginBottom: '20px',
      paddingBottom: '12px',
      borderBottom: '1px dashed #e2e8f0'
  },
  scrollableContent: {
      // אין צורך בהגדרות גלילה נוספות כאן, modalBody מטפל בזה
  },
  analysisText: {
    lineHeight: '1.7',
    color: '#334155',
    fontSize: '1.05rem'
  },
  paragraph: {
    marginBottom: '16px',
    textAlign: 'right'
  },
  jsonPre: {
    whiteSpace: 'pre-wrap', 
    textAlign: 'left', 
    direction: 'ltr',
    backgroundColor: '#f1f5f9',
    padding: '16px',
    borderRadius: '8px',
    fontSize: '0.9rem',
    color: '#475569',
    overflowX: 'auto'
  }
};