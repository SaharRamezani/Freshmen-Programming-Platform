import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Radio, Spin, Typography, Card } from 'antd';
import { getToken } from '../../services/authService';
import './TutorialPage.css';

const { Title } = Typography;

const TutorialPage = () => {
    const [markdown, setMarkdown] = useState('');
    const [language, setLanguage] = useState('en');
    const [loading, setLoading] = useState(true);

    const getRoleFromToken = () => {
        try {
            const token = getToken();
            if (!token || token === "dev_mode_token") return null;
            const payload = JSON.parse(atob(token.split(".")[1]));
            return payload.role || null;
        } catch {
            return null;
        }
    };

    const role = getRoleFromToken();

    useEffect(() => {
        const fetchTutorial = async () => {
            setLoading(true);
            try {
                let roleFile = 'student_tutorial.md';
                // Admin also sees teacher tutorial
                if (role === 'teacher' || role === 'admin') {
                    roleFile = 'teacher_tutorial.md';
                } else if (role === 'student') {
                    roleFile = 'student_tutorial.md';
                }

                const path = `/tutorials/${language}/${roleFile}`;
                
                const response = await fetch(path);
                if (response.ok) {
                    const text = await response.text();
                    setMarkdown(text);
                } else {
                    setMarkdown('# Tutorial not found\nSorry, the tutorial file could not be loaded.');
                }
            } catch (error) {
                console.error("Failed to load tutorial:", error);
                setMarkdown('# Error\nFailed to load tutorial content.');
            } finally {
                setLoading(false);
            }
        };

        if (role) {
            fetchTutorial();
        }
    }, [language, role]);

    if (!role) {
        return <div className="tutorial-container">Please log in to view tutorials.</div>;
    }

    return (
        <div className="tutorial-page-container">
            <div className="tutorial-header-controls">
                <Title level={2} style={{ margin: 0 }}>
                    {role === 'student' ? 'Student Tutorial' : 'Teacher Tutorial'}
                </Title>
                <Radio.Group 
                    value={language} 
                    onChange={(e) => setLanguage(e.target.value)}
                    buttonStyle="solid"
                >
                    <Radio.Button value="en">English</Radio.Button>
                    <Radio.Button value="it">Italiano</Radio.Button>
                </Radio.Group>
            </div>
            
            <Card className="tutorial-content-card">
                {loading ? (
                    <div className="tutorial-loading">
                        <Spin size="large" />
                    </div>
                ) : (
                    <div className="markdown-body">
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                img: ({ src, alt, ...props }) => {
                                    // Resolve relative image paths to the correct public path
                                    let resolvedSrc = src;
                                    if (src && !src.startsWith('http') && !src.startsWith('/')) {
                                        resolvedSrc = `/tutorials/images/${src.replace(/^(\.\.\/)*images\//, '')}`;
                                    }
                                    return <img src={resolvedSrc} alt={alt} {...props} />;
                                }
                            }}
                        >
                            {markdown}
                        </ReactMarkdown>
                    </div>
                )}
            </Card>
        </div>
    );
};

export default TutorialPage;
