import React from 'react';
import { HeartPulse, User, FileUp, Zap } from 'lucide-react';
import MealHistory from './MealHistory';

const Sidebar = ({
    users,
    selectedUserId,
    setSelectedUserId,
    setFile,
    file,
    handleAnalyze,
    loading
}) => {
    return (
        <aside className="sidebar">
            <div className="brand">
                <HeartPulse color="#2563eb" size={28} />
                <h2>Clinical AI</h2>
            </div>

            <div className="control-group">
                <label>
                    <User size={14} style={{ display: 'inline', marginRight: 5 }} />
                    Select Patient
                </label>
                <select
                    onChange={(e) => setSelectedUserId(Number(e.target.value))}
                    value={selectedUserId || ""}
                >
                    {users.map(u => (
                        <option key={u.user_id} value={u.user_id}>
                            {u.full_name} {u.is_pregnant ? '(Pregnant)' : ''}
                        </option>
                    ))}
                </select>
            </div>

            <div className="control-group">
                <label>
                    <FileUp size={14} style={{ display: 'inline', marginRight: 5 }} />
                    Upload Meal Image
                </label>

                {/* עיצוב כפתור העלאה מותאם אישית */}
                <div className="file-upload-box">
                    <input type="file" onChange={(e) => setFile(e.target.files[0])} />
                    <div className="upload-placeholder">
                        {file ? file.name : "Click or Drag image here"}
                    </div>
                </div>

                {selectedUserId && <MealHistory userId={selectedUserId} />}

                <button
                    onClick={handleAnalyze}
                    disabled={loading || !file}
                    className="analyze-btn"
                >
                    {loading ? (
                        <>Processing...</>
                    ) : (
                        <><Zap size={18} /> Analyze Meal</>
                    )}
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
