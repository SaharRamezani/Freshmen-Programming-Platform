import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
    createMatchSetting,
    updateMatchSetting,
    publishMatchSetting,
    tryMatchSetting,
    fetchMatchSetting,
} from '../../../services/matchSettingsService';

const DEFAULT_STUDENT_CODE = `#include <iostream>
using namespace std;

int main(){
    return 0;
}
`;

const useCreateMatchSetting = () => {
    const navigate = useNavigate();
    const { id } = useParams();
    const isEditMode = Boolean(id);

    // Form state
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        reference_solution: '// Reference solution for the match.\n#include <iostream>\n\nint main() {\n    std::cout << "Hello, World!";\n    return 0;\n}',
        student_code: DEFAULT_STUDENT_CODE,
        function_name: '',
        function_type: 'int',
        function_inputs: '',
        language: 'cpp',
    });

    const [publicTests, setPublicTests] = useState([]);
    const [privateTests, setPrivateTests] = useState([]);

    const [matchDetailsExpanded, setMatchDetailsExpanded] = useState(true);
    const [configExpanded, setConfigExpanded] = useState(false);
    const [validationResults, setValidationResults] = useState(null);
    const [alert, setAlert] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isTrying, setIsTrying] = useState(false);
    const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
    const [inputsList, setInputsList] = useState([]);

    // Update formData.function_inputs whenever inputsList changes
    useEffect(() => {
        setFormData(prev => ({
            ...prev,
            function_inputs: JSON.stringify(inputsList)
        }));
        setHasUnsavedChanges(true);
    }, [inputsList]);

    const handleAddInputRow = useCallback(() => {
        setInputsList(prev => [...prev, { type: 'int', name: '' }]);
    }, []);

    const handleRemoveInputRow = useCallback((index) => {
        setInputsList(prev => {
            const newList = [...prev];
            newList.splice(index, 1);
            return newList;
        });
    }, []);

    const handleInputChangeRow = useCallback((index, field, value) => {
        setInputsList(prev => {
            const newList = [...prev];
            newList[index][field] = value;
            return newList;
        });
    }, []);

    // Load existing match setting if in edit mode
    useEffect(() => {
        if (isEditMode) {
            fetchMatchSetting(id)
                .then((data) => {
                    setFormData({
                        title: data.title,
                        description: data.description,
                        reference_solution: data.reference_solution,
                        student_code: data.student_code || DEFAULT_STUDENT_CODE,
                        function_name: data.function_name || '',
                        function_type: data.function_type || 'output',
                        function_inputs: data.function_inputs || '',
                        language: data.language || 'cpp',
                    });

                    // Parse function inputs if they exist
                    if (data.function_inputs) {
                        try {
                            const parsed = JSON.parse(data.function_inputs);
                            if (Array.isArray(parsed)) {
                                setInputsList(parsed);
                            }
                        } catch (e) {
                            console.error("Failed to parse function inputs", e);
                        }
                    }

                    const pubTests = data.tests.filter(t => t.scope === 'public');
                    const privTests = data.tests.filter(t => t.scope === 'private');

                    setPublicTests(pubTests);
                    setPrivateTests(privTests);
                    setHasUnsavedChanges(false);
                })
                .catch((error) => {
                    setAlert({ type: 'error', message: error.message });
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                });
        }
    }, [id, isEditMode]);

    const handleInputChange = useCallback((field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
        setHasUnsavedChanges(true);
    }, []);

    const handleAddPublicTest = useCallback(() => {
        setPublicTests(prev => [...prev, { test_in: '', test_out: '' }]);
        setHasUnsavedChanges(true);
    }, []);

    const handleAddPrivateTest = useCallback(() => {
        setPrivateTests(prev => [...prev, { test_in: '', test_out: '' }]);
        setHasUnsavedChanges(true);
    }, []);

    const handleTestChange = useCallback((index, field, value, isPublic) => {
        const updater = (prev) => {
            const tests = [...prev];
            tests[index][field] = value;
            return tests;
        };
        isPublic ? setPublicTests(updater) : setPrivateTests(updater);
        setHasUnsavedChanges(true);
    }, []);

    const handleDeleteTest = useCallback((index, isPublic) => {
        const filter = (prev) => prev.filter((_, i) => i !== index);
        isPublic ? setPublicTests(filter) : setPrivateTests(filter);
        setHasUnsavedChanges(true);
    }, []);

    const handleTry = useCallback(async () => {
        setIsTrying(true);
        setValidationResults(null);
        setAlert(null);

        const allTests = [
            ...publicTests.map(t => ({ ...t, scope: 'public' })),
            ...privateTests.map(t => ({ ...t, scope: 'private' })),
        ];

        // No test cases: still compile to check for errors, but warn user
        if (allTests.length === 0) {
            try {
                const result = await tryMatchSetting({
                    reference_solution: formData.reference_solution,
                    language: formData.language,
                    tests: allTests,
                });

                if (result.compilation_error) {
                    setValidationResults(result);
                    setAlert({ type: 'error', message: 'Compilation failed' });
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                } else {
                    setValidationResults({ ...result, message: 'Code compiled successfully' });
                    setAlert({
                        type: 'warning',
                        message: 'Code compiled successfully, but no test cases to run. Add test cases to validate your solution.',
                    });
                }
            } catch (error) {
                setAlert({ type: 'error', message: error.message });
                window.scrollTo({ top: 0, behavior: 'smooth' });
            } finally {
                setIsTrying(false);
            }
            return;
        }

        try {
            const result = await tryMatchSetting({
                reference_solution: formData.reference_solution,
                language: formData.language,
                tests: allTests,
            });

            // Enrich results with scope info (backend doesn't return it)
            if (result.test_results) {
                result.test_results = result.test_results.map((r, i) => ({
                    ...r,
                    scope: allTests[i]?.scope || 'public',
                }));
            }

            setValidationResults(result);

            if (result.success) {
                setAlert(null);
            } else {
                // Don't show a top alert or scroll — the summary banner is enough
                setAlert(null);
            }
        } catch (error) {
            setAlert({ type: 'error', message: error.message });
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } finally {
            setIsTrying(false);
        }
    }, [publicTests, privateTests, formData.reference_solution, formData.language]);

    const handleSaveDraft = useCallback(async () => {
        setIsSubmitting(true);
        setAlert(null);

        const allTests = [
            ...publicTests.map(t => ({ ...t, scope: 'public' })),
            ...privateTests.map(t => ({ ...t, scope: 'private' })),
        ];

        const payload = {
            ...formData,
            tests: allTests,
        };

        try {
            if (isEditMode) {
                await updateMatchSetting(id, payload);
                setAlert({ type: 'success', message: 'Match setting updated as draft' });
            } else {
                const created = await createMatchSetting(payload);
                setAlert({ type: 'success', message: 'Match setting saved as draft' });
                navigate(`/match-settings/${created.match_set_id}/edit`);
            }
            setHasUnsavedChanges(false);
        } catch (error) {
            setAlert({ type: 'error', message: error.message });
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } finally {
            setIsSubmitting(false);
        }
    }, [isEditMode, id, formData, publicTests, privateTests, navigate]);

    const handlePublish = useCallback(async () => {
        // Validate required fields
        if (!formData.title || formData.title.trim().length < 5) {
            setAlert({ type: 'error', message: 'Match Title is required and must be at least 5 characters long' });
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }

        if (!formData.description || formData.description.trim().length < 10) {
            setAlert({ type: 'error', message: 'Description is required and must be at least 10 characters long' });
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }

        if (!formData.reference_solution) {
            setAlert({ type: 'error', message: 'Reference solution is required' });
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }

        if (publicTests.length === 0) {
            setAlert({ type: 'error', message: 'At least one public test case is required' });
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }

        setIsSubmitting(true);
        setAlert(null);

        try {
            // First save/update as draft
            const allTests = [
                ...publicTests.map(t => ({ ...t, scope: 'public' })),
                ...privateTests.map(t => ({ ...t, scope: 'private' })),
            ];

            const payload = {
                ...formData,
                tests: allTests,
                publish: true,
            };

            if (isEditMode) {
                await updateMatchSetting(id, payload);
            } else {
                await createMatchSetting(payload);
            }

            // Publish handling is now done atomically in create/update
            // await publishMatchSetting(matchSetId);

            setAlert({ type: 'success', message: 'Match setting published successfully!' });
            setHasUnsavedChanges(false);

            setTimeout(() => {
                navigate('/match-settings');
            }, 1500);
        } catch (error) {
            setAlert({ type: 'error', message: error.message });
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } finally {
            setIsSubmitting(false);
        }
    }, [formData, publicTests, privateTests, isEditMode, id, navigate]);

    const generateBoilerplate = useCallback(() => {
        if (!formData.function_name) {
            setAlert({ type: 'error', message: 'Please enter a function name first' });
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }

        try {
            const inputs = inputsList;
            const includes = ['#include <iostream>'];
            if (inputs.some(inp => inp.type && inp.type.includes('vector'))) {
                includes.push('#include <vector>');
            }
            if (inputs.some(inp => inp.type && inp.type.includes('string'))) {
                includes.push('#include <string>');
            }

            const returnType = formData.function_type === 'output' ? 'int' : (formData.function_type || 'void');
            const params = inputs.map(inp => `${inp.type} ${inp.name}`).join(', ');
            const functionSignature = `${returnType} ${formData.function_name}(${params})`;

            const functionBody = `${functionSignature} {\n    // TODO: Implement your solution here\n    ${returnType === 'int' ? 'int result = 0;\n    return result;' : ''}\n}`;

            let mainBody = 'int main() {\n    // Automatic Input Handling\n';

            inputs.forEach(inp => {
                if (inp.type === 'int' || inp.type === 'double' || inp.type === 'float') {
                    mainBody += `    ${inp.type} ${inp.name};\n`;
                    mainBody += `    std::cin >> ${inp.name};\n`;
                } else if (inp.type.includes('vector')) {
                    mainBody += `    int ${inp.name}_size;\n`;
                    mainBody += `    std::cin >> ${inp.name}_size;\n`;
                    mainBody += `    ${inp.type} ${inp.name}(${inp.name}_size);\n`;
                    mainBody += `    for (int i = 0; i < ${inp.name}_size; ++i) {\n`;
                    mainBody += `        std::cin >> ${inp.name}[i];\n`;
                    mainBody += `    }\n`;
                } else if (inp.type.includes('string')) {
                    mainBody += `    ${inp.type} ${inp.name};\n`;
                    mainBody += `    std::cin >> ${inp.name};\n`;
                }
            });

            // Function call
            mainBody += '\n    // Call solve function\n';
            const argNames = inputs.map(inp => inp.name).join(', ');

            if (returnType !== 'void') {
                mainBody += `    ${returnType} result = ${formData.function_name}(${argNames});\n`;
                mainBody += '\n    // Automatic Output Handling\n';
                if (returnType.includes('vector')) {
                    mainBody += `    for (size_t i = 0; i < result.size(); ++i) {\n`;
                    mainBody += `        std::cout << result[i] << (i == result.size() - 1 ? "" : " ");\n`;
                    mainBody += `    }\n`;
                    mainBody += `    std::cout << std::endl;\n`;
                } else {
                    mainBody += '    std::cout << result << std::endl;\n';
                }
            } else {
                mainBody += `    ${formData.function_name}(${argNames});\n`;
            }

            mainBody += '    return 0;\n}';

            const boilerplate = `${includes.join('\n')}\n\n// Student fills in this function\n${functionBody}\n\n${mainBody}`;

            handleInputChange('student_code', boilerplate);
            setAlert({ type: 'success', message: 'Boilerplate code generated successfully!' });
        } catch (error) {
            setAlert({ type: 'error', message: 'Error generating boilerplate: ' + error.message });
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }, [formData.function_name, formData.function_type, inputsList, handleInputChange]);

    // Auto-save on page exit
    useEffect(() => {
        const handleBeforeUnload = (e) => {
            if (hasUnsavedChanges && !isEditMode) {
                handleSaveDraft();
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [hasUnsavedChanges, isEditMode, handleSaveDraft]);


    return {
        isEditMode,
        formData,
        publicTests,
        privateTests,
        matchDetailsExpanded,
        setMatchDetailsExpanded,
        configExpanded,
        setConfigExpanded,
        validationResults,
        alert,
        setAlert,
        isSubmitting,
        isTrying,
        inputsList,
        handlers: {
            handleInputChange,
            handleAddPublicTest,
            handleAddPrivateTest,
            handleTestChange,
            handleDeleteTest,
            handleTry,
            handleSaveDraft,
            handlePublish,
            generateBoilerplate,
            handleInputChangeRow,
            handleRemoveInputRow,
            handleAddInputRow,
            handleDismissAlert: () => setAlert(null),
            onBack: () => navigate('/home'),
        }
    };
};

export default useCreateMatchSetting;
