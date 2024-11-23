import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import '../styles/main.css';
import Chart from './Chart';
import DisplayAverageRating from './DisplayAverageRating.js';
import SubmitRating from './SubmitRating.js';
import Comment from './Comment.js';

const ProfessorPage = () => {
  const { professorId } = useParams();
  const [professorData, setProfessorData] = useState(null); // Stores course data
  const [instructorName, setInstructorName] = useState(""); // Exact name from DB
  const [passFailData, setPassFailData] = useState({ passRate: 0, failRate: 0 });
  const [error, setError] = useState(null);

  // Format professorId to "Last Name, First Name" for query
  const formatName = (id) => {
    if (!id) return null;
    const [lastName, firstName] = id.split('-');
    if (!lastName || !firstName) return null;
    return `${lastName.charAt(0).toUpperCase() + lastName.slice(1)}, ${firstName.charAt(0).toUpperCase() + firstName.slice(1)}`;
  };

  const formattedInstructorName = formatName(professorId);

  // Fetch professor data
  useEffect(() => {
    const fetchProfessorData = async () => {
      try {
        // Call professor endpoint with formatted name
        const response = await fetch(`/service/professor?name=${encodeURIComponent(formattedInstructorName)}`);
        if (!response.ok) throw new Error("Professor not found.");
        
        const data = await response.json();
        setProfessorData(data.courses);
        setInstructorName(data.professor);
      } catch (err) {
        setError(err.message);
      }
    };

    fetchProfessorData();
  }, [formattedInstructorName]);

  if (error) return <p>{error}</p>;
  if (!professorData) return <p>Loading...</p>;

  return (
    <main className="professor-page container">
      <div className="professor-header">
        <h1>{instructorName}</h1>
        <hr className="professor-line"></hr>
      </div>

      <DisplayAverageRating className={null} instructorName={instructorName} searchBy="instructor_name" />
      
      <div className="info-sections">
        <section className="grade-distribution-graph">
          <h2>Grade Distribution Graph</h2>
          <Chart className={null} instructorName={instructorName} searchBy="instructor_name" />
        </section>


      </div>

      <section className="reviews">
        <h2>Leave a Rating</h2>
        <SubmitRating className={null} instructorName={instructorName} searchBy="instructor_name" />
      </section>

      <Comment reviewType={instructorName} />
    </main>
  );
}

export default ProfessorPage;
