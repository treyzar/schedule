'use client';

import { useState, useEffect, FormEvent } from 'react';

// ==============================================================================
// 1. ИНТЕРФЕЙСЫ ДЛЯ ДАННЫХ (Описываем, как выглядят данные от API)
// ==============================================================================
interface SubjectData {
  stream: { id: number; title: string } | null;
  program: { id: number; title: string } | null;
}

interface AllSubjectsResponse {
  subjects_found: string[];
  data: Record<string, SubjectData>;
  errors: any[];
  total_subjects_found: number;
}

// ==============================================================================
// 2. ОСНОВНОЙ КОМПОНЕНТ ПАРСЕРА
// ==============================================================================
export default function ParsingInteractive() {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [subjectsData, setSubjectsData] = useState<AllSubjectsResponse | null>(null);

  /**
   * Функция для получения данных по предметам с бэкенда.
   */
  const fetchSubjectsData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/parse_avatar/all-subjects/', {
        credentials: 'include', // <-- ВАЖНО! Отправляем cookie вместе с запросом
      });

      if (response.status === 401) {
        setIsLoggedIn(false);
        setIsLoading(false);
        return;
      }

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Не удалось загрузить данные по предметам.');
      }

      const data: AllSubjectsResponse = await response.json();
      setSubjectsData(data);
      setIsLoggedIn(true);
    } catch (err: any) {
      // Игнорируем ошибку "Failed to fetch" при первой загрузке, если сервер выключен
      if (!(err instanceof TypeError && err.message === 'Failed to fetch')) {
        setError(err.message);
      }
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Функция для обработки отправки формы входа.
   */
  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/parse_avatar/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
        credentials: 'include', // <-- ВАЖНО! Разрешаем установку cookie с другого домена
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          result.message || 'Вход не удался. Проверьте правильность логина и пароля.'
        );
      }

      await fetchSubjectsData();
    } catch (err: any) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setSubjectsData(null);
    setUsername('');
    setPassword('');
    setError(null);
  };

  useEffect(() => {
    fetchSubjectsData();
  }, []);

  // --- РЕНДЕРИНГ ---

  if (isLoading) {
    return (
      <div style={styles.container}>
        <p style={styles.loadingText}>Загрузка...</p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.header}>Парсер данных Skyeng</h1>

      {error && <p style={styles.error}>{error}</p>}

      {!isLoggedIn ? (
        <form onSubmit={handleLogin} style={styles.form}>
          <h2 style={styles.subHeader}>Вход в аккаунт</h2>
          <div style={styles.inputGroup}>
            <label htmlFor="username">Логин:</label>
            <input
              id="username"
              type="email"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="ivan.khristoforov@sinhub.ru"
              style={styles.input}
              required
            />
          </div>
          <div style={styles.inputGroup}>
            <label htmlFor="password">Пароль:</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={styles.input}
              required
            />
          </div>
          <button type="submit" style={styles.button} disabled={isLoading}>
            Войти
          </button>
        </form>
      ) : (
        <div>
          <div style={styles.dataHeader}>
            <h2 style={styles.subHeader}>Найденные предметы</h2>
            <button onClick={handleLogout} style={{ ...styles.button, ...styles.logoutButton }}>
              Выйти
            </button>
          </div>

          {subjectsData && subjectsData.total_subjects_found > 0 ? (
            <>
              <p style={styles.summaryText}>
                Всего найдено предметов с активными программами:{' '}
                <strong>{subjectsData.total_subjects_found}</strong>
              </p>
              <div style={styles.grid}>
                {Object.entries(subjectsData.data).map(([subjectName, subjectData]) => (
                  <div key={subjectName} style={styles.card}>
                    <h3 style={styles.cardHeader}>{subjectName.toUpperCase()}</h3>
                    {subjectData.stream ? (
                      <p>
                        <strong>Поток:</strong> {subjectData.stream.title}
                      </p>
                    ) : subjectData.program ? (
                      <p>
                        <strong>Программа:</strong> {subjectData.program.title}
                      </p>
                    ) : (
                      <p style={styles.noDataText}>Нет активных программ.</p>
                    )}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p>Активных предметов с программами или потоками не найдено.</p>
          )}
        </div>
      )}
    </div>
  );
}

// ==============================================================================
// 3. СТИЛИ (для наглядности, можете заменить их на свои классы Tailwind/CSS)
// ==============================================================================
const styles: { [key: string]: React.CSSProperties } = {
  container: {
    fontFamily: 'system-ui, sans-serif',
    maxWidth: '900px',
    margin: '40px auto',
    padding: '20px',
    backgroundColor: '#f9f9f9',
    borderRadius: '8px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
  },
  header: { textAlign: 'center', color: '#222', marginBottom: '30px' },
  subHeader: {
    color: '#333',
    borderBottom: '2px solid #eee',
    paddingBottom: '10px',
    marginBottom: '20px',
  },
  loadingText: { textAlign: 'center', fontSize: '18px', color: '#555' },
  error: {
    color: '#D8000C',
    backgroundColor: '#FFD2D2',
    border: '1px solid #D8000C',
    padding: '15px',
    borderRadius: '5px',
    margin: '20px 0',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
    maxWidth: '400px',
    margin: '20px auto',
    padding: '30px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    backgroundColor: 'white',
  },
  inputGroup: { display: 'flex', flexDirection: 'column', gap: '5px' },
  input: { padding: '12px', border: '1px solid #ccc', borderRadius: '5px', fontSize: '16px' },
  button: {
    padding: '12px 15px',
    border: 'none',
    borderRadius: '5px',
    backgroundColor: '#007BFF',
    color: 'white',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: 'bold',
  },
  dataHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  logoutButton: { backgroundColor: '#6c757d' },
  summaryText: { fontSize: '16px', color: '#444', marginBottom: '20px' },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '20px',
    marginTop: '20px',
  },
  card: {
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '20px',
    backgroundColor: 'white',
    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
    transition: 'transform 0.2s',
  },
  cardHeader: { margin: '0 0 15px 0', color: '#0056b3', fontSize: '18px' },
  noDataText: { fontStyle: 'italic', color: '#888' },
};
