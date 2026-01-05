import React, { useEffect, useState } from 'react';
import axios from 'axios';

// קומפוננטה להצגת פרטי ארוחה אחת (Modal או תצוגה מורחבת)
const MealDetails = ({ meal, onClose }) => {
  // מנסים לפרסר את ה-JSON של הניתוח, או מציגים כטקסט אם זה לא JSON
  let analysisData = null;
  try {
    analysisData = typeof meal.ai_analysis_summary === 'string' 
      ? JSON.parse(meal.ai_analysis_summary) 
      : meal.ai_analysis_summary;
  } catch (e) {
    analysisData = { text: meal.ai_analysis_summary };
  }

  return (
    <div style={styles.modalOverlay}>
      <div style={styles.modalContent}>
        <button onClick={onClose} style={styles.closeButton}>X</button>
        <h3>דוח ארוחה מתאריך {new Date(meal.created_at).toLocaleDateString()}</h3>
        <div style={styles.scrollableContent}>
            {/* כאן אפשר לעצב יפה את המידע */}
            <pre style={{whiteSpace: 'pre-wrap', textAlign: 'left', direction: 'ltr'}}>
                {JSON.stringify(analysisData, null, 2)}
            </pre>
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
      // עדכן את ה-URL לכתובת הלמבדה שלך
      const response = await axios.get(`https://ldclmiawsh.execute-api.us-east-1.amazonaws.com/default/history/${userId}`);
      setMeals(response.data);
    } catch (error) {
      console.error("Error fetching history:", error);
      alert("לא הצלחנו לטעון את ההיסטוריה");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <p>טוען היסטוריה...</p>;
  if (meals.length === 0) return <p>אין עדיין ארוחות שמורות.</p>;

  return (
    <div style={styles.container}>
      <h2>הארוחות שלי</h2>
      <div style={styles.grid}>
        {meals.map((meal) => (
          <div key={meal.meal_id} style={styles.card} onClick={() => setSelectedMeal(meal)}>
            <div style={styles.cardHeader}>
                📅 {new Date(meal.created_at).toLocaleDateString()}
            </div>
            <div style={styles.cardBody}>
                🕒 {new Date(meal.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                <br/>
                <span style={{fontSize: '0.8rem', color: '#666'}}>לחץ לפרטים מלאים</span>
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

const styles = {
  container: { marginTop: '20px', padding: '10px' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '15px' },
  card: { 
    border: '1px solid #ddd', borderRadius: '8px', padding: '15px', 
    cursor: 'pointer', backgroundColor: '#fff', boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    transition: 'transform 0.2s'
  },
  cardHeader: { fontWeight: 'bold', marginBottom: '5px', color: '#2c3e50' },
  modalOverlay: {
    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000
  },
  modalContent: {
    backgroundColor: 'white', padding: '20px', borderRadius: '10px',
    width: '90%', maxWidth: '600px', maxHeight: '80vh', overflowY: 'auto', position: 'relative'
  },
  closeButton: {
    position: 'absolute', top: '10px', left: '10px', 
    background: 'red', color: 'white', border: 'none', borderRadius: '50%', width: '30px', height: '30px', cursor: 'pointer'
  }
};