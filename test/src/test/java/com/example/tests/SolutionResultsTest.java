package com.example.tests;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.Duration;
import java.util.List;

import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.junit.jupiter.api.MethodOrderer.OrderAnnotation;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import com.example.pages.LoginPO;
import com.example.pages.SolutionResultsPO;

@TestMethodOrder(OrderAnnotation.class)
public class SolutionResultsTest extends BaseTest {
    private static LoginPO loginPO;
    private static SolutionResultsPO solutionResultsPO;
    
    private static final String TEST_SOLUTION_ID = "1";

    @BeforeAll
    public static void setUpTest() {
        loginPO = new LoginPO(driver);
        solutionResultsPO = new SolutionResultsPO(driver);
    }

    @AfterAll
    public static void tearDownTest() {
        loginPO = null;
        solutionResultsPO = null;
    }

    @BeforeEach
    public void setUpEachTest() throws InterruptedException {
        navigateTo("/login");
        clearLocalStorage();
        driver.navigate().refresh();
        loginAndNavigateToResults();
        Thread.sleep(500);
    }

    private void loginAndNavigateToResults() throws InterruptedException {
        loginPO.loginAsPreconfiguredStudent();
        Thread.sleep(500);
        navigateTo("/solution-results/" + TEST_SOLUTION_ID);
        solutionResultsPO.waitForPageLoad();
    }

    @Test
    @Order(1)
    @DisplayName("Scenario 1: Displaying the header and total score")
    public void testDisplayingHeaderAndTotalScore() throws InterruptedException {
        assertTrue(solutionResultsPO.isHeaderVisible(), "Header should be visible");
        
        String pageTitle = solutionResultsPO.getPageTitle();
        assertNotNull(pageTitle, "Page title should be visible");
        assertTrue(pageTitle.contains("Solution Review"), "Page title should contain 'Solution Review'");
        assertTrue(pageTitle.contains("Game Session"), "Page title should contain 'Game Session'");
        
        System.out.println("✓ Page title: " + pageTitle);
        
        assertTrue(solutionResultsPO.isScoreDisplayVisible(), "Score display should be visible");
        
        String totalScore = solutionResultsPO.getTotalScoreText();
        assertNotNull(totalScore, "Total score should be displayed");
        assertTrue(totalScore.contains("/"), "Score should be in format 'X/Y'");
        
        System.out.println("✓ Total score displayed: " + totalScore);
    }

    @Test
    @Order(2)
    @DisplayName("Scenario 2: Viewing the submitted source code with syntax highlighting")
    public void testViewingSourceCodeWithSyntaxHighlighting() throws InterruptedException {
        assertTrue(solutionResultsPO.isCodeBlockVisible(), "Code block should be visible");
        
        String codeBlockTitle = solutionResultsPO.getCodeBlockTitle();
        assertNotNull(codeBlockTitle, "Code block title should be visible");
        assertTrue(codeBlockTitle.contains("Solution") || codeBlockTitle.contains("Results"), 
            "Code block should be labeled as solution or results");
        
        System.out.println("✓ Code block title: " + codeBlockTitle);
        
        String codeContent = solutionResultsPO.getCodeContent();
        assertNotNull(codeContent, "Code content should be displayed");
        assertTrue(codeContent.length() > 0, "Code content should not be empty");
        
        System.out.println("✓ Code content is displayed");
    }

    @Test
    @Order(3)
    @DisplayName("Scenario 3: Reviewing test cases sections")
    public void testReviewingTestCasesSections() throws InterruptedException {
        boolean publicVisible = solutionResultsPO.isPublicTeacherTestsSectionVisible();
        boolean privateVisible = solutionResultsPO.isPrivateTeacherTestsSectionVisible();
        boolean studentVisible = solutionResultsPO.isStudentTestsSectionVisible();
        
        assertTrue(publicVisible || privateVisible || studentVisible, 
            "At least one test section should be visible");
        
        if (publicVisible) {
            String publicHeader = solutionResultsPO.getPublicTestsSectionHeader();
            assertNotNull(publicHeader, "Public tests header should be visible");
            assertTrue(publicHeader.toUpperCase().contains("PUBLIC"), 
                "Public tests section should be labeled correctly");
            System.out.println("✓ PUBLIC TEACHER TESTS section visible: " + publicHeader);
        }
        
        if (privateVisible) {
            String privateHeader = solutionResultsPO.getPrivateTestsSectionHeader();
            assertNotNull(privateHeader, "Private tests header should be visible");
            assertTrue(privateHeader.toUpperCase().contains("PRIVATE"), 
                "Private tests section should be labeled correctly");
            System.out.println("✓ PRIVATE TEACHER TESTS section visible: " + privateHeader);
        }
        
        if (studentVisible) {
            String studentHeader = solutionResultsPO.getStudentTestsSectionHeader();
            assertNotNull(studentHeader, "Student tests header should be visible");
            assertTrue(studentHeader.toUpperCase().contains("STUDENT"), 
                "Student tests section should be labeled correctly");
            System.out.println("✓ STUDENT PROVIDED TESTS section visible: " + studentHeader);
        }
    }

    @Test
    @Order(4)
    @DisplayName("Scenario 4: Reviewing successful test cases")
    public void testReviewingSuccessfulTestCases() throws InterruptedException {
        List<WebElement> publicTests = solutionResultsPO.getPublicTestResults();
        List<WebElement> privateTests = solutionResultsPO.getPrivateTestResults();
        List<WebElement> studentTests = solutionResultsPO.getStudentTestResults();
        
        WebElement passedTest = null;
        String sectionName = "";
        
        for (WebElement test : publicTests) {
            if (solutionResultsPO.isTestPassed(test)) {
                passedTest = test;
                sectionName = "PUBLIC TEACHER TESTS";
                break;
            }
        }
        
        if (passedTest == null) {
            for (WebElement test : privateTests) {
                if (solutionResultsPO.isTestPassed(test)) {
                    passedTest = test;
                    sectionName = "PRIVATE TEACHER TESTS";
                    break;
                }
            }
        }
        
        if (passedTest == null) {
            for (WebElement test : studentTests) {
                if (solutionResultsPO.isTestPassed(test)) {
                    passedTest = test;
                    sectionName = "STUDENT PROVIDED TESTS";
                    break;
                }
            }
        }
        
        if (passedTest != null) {
            String input = solutionResultsPO.getTestInput(passedTest);
            assertNotNull(input, "Test input should be displayed");
            System.out.println("✓ Input displayed: " + input);
            
            String expectedOutput = solutionResultsPO.getTestExpectedOutput(passedTest);
            assertNotNull(expectedOutput, "Expected output should be displayed");
            assertTrue(expectedOutput.contains("Exp"), "Expected output should be preceded by 'Exp'");
            System.out.println("✓ Expected output displayed: " + expectedOutput);
            
            String status = solutionResultsPO.getTestStatus(passedTest);
            assertTrue(status.contains("Passed"), "Status should show 'Passed'");
            System.out.println("✓ Status: " + status);
            
            assertTrue(solutionResultsPO.hasPassedIcon(passedTest), 
                "Should show green checkmark icon for passed test");
            System.out.println("✓ Green checkmark icon displayed for passed test in " + sectionName);
        } else {
            System.out.println("⚠ No passed test cases found to verify");
        }
    }

    @Test
    @Order(5)
    @DisplayName("Scenario 5: Debugging a failed test case")
    public void testDebuggingFailedTestCase() throws InterruptedException {
        List<WebElement> publicTests = solutionResultsPO.getPublicTestResults();
        List<WebElement> privateTests = solutionResultsPO.getPrivateTestResults();
        List<WebElement> studentTests = solutionResultsPO.getStudentTestResults();
        
        WebElement failedTest = null;
        String sectionName = "";
        
        for (WebElement test : privateTests) {
            if (solutionResultsPO.isTestFailed(test)) {
                failedTest = test;
                sectionName = "PRIVATE TEACHER TESTS";
                break;
            }
        }
        
        if (failedTest == null) {
            for (WebElement test : publicTests) {
                if (solutionResultsPO.isTestFailed(test)) {
                    failedTest = test;
                    sectionName = "PUBLIC TEACHER TESTS";
                    break;
                }
            }
        }
        
        if (failedTest == null) {
            for (WebElement test : studentTests) {
                if (solutionResultsPO.isTestFailed(test)) {
                    failedTest = test;
                    sectionName = "STUDENT PROVIDED TESTS";
                    break;
                }
            }
        }
        
        if (failedTest != null) {
            assertTrue(solutionResultsPO.hasFailedIcon(failedTest), 
                "Should show red X icon for failed test");
            System.out.println("✓ Red X icon displayed for failed test in " + sectionName);
            
            String status = solutionResultsPO.getTestStatus(failedTest);
            assertTrue(status.contains("Failed"), "Status should show 'Failed'");
            System.out.println("✓ Status: " + status);
            
            String expectedOutput = solutionResultsPO.getTestExpectedOutput(failedTest);
            assertNotNull(expectedOutput, "Expected output should be displayed");
            assertTrue(expectedOutput.contains("Exp"), "Expected output should be labeled with 'Exp'");
            System.out.println("✓ Expected output: " + expectedOutput);
            
            String actualOutput = solutionResultsPO.getTestActualOutput(failedTest);
            assertNotNull(actualOutput, "Actual output should be displayed for debugging");
            assertTrue(actualOutput.contains("Output"), "Actual output should be labeled with 'Output'");
            System.out.println("✓ Actual output for debugging: " + actualOutput);
        } else {
            System.out.println("⚠ No failed test cases found to verify");
        }
    }

    @Test
    @Order(6)
    @DisplayName("Scenario 6: Verifying student-provided test cases")
    public void testVerifyingStudentProvidedTestCases() throws InterruptedException {
        if (!solutionResultsPO.isStudentTestsSectionVisible()) {
            System.out.println("⚠ No student provided tests section visible - test skipped");
            return;
        }
        
        List<WebElement> studentTests = solutionResultsPO.getStudentTestResults();
        
        if (studentTests.isEmpty()) {
            System.out.println("⚠ No student test cases found");
            return;
        }
        
        WebElement studentTest = studentTests.get(0);
        
        String input = solutionResultsPO.getTestInput(studentTest);
        assertNotNull(input, "Student test input should be displayed");
        System.out.println("✓ Student test input: " + input);
        
        String expectedOutput = solutionResultsPO.getTestExpectedOutput(studentTest);
        assertNotNull(expectedOutput, "Student test expected output should be displayed");
        System.out.println("✓ Student test expected output: " + expectedOutput);
        
        String status = solutionResultsPO.getTestStatus(studentTest);
        assertNotNull(status, "Student test status should be displayed");
        assertTrue(status.equals("Passed") || status.equals("Failed"), 
            "Status should be either 'Passed' or 'Failed'");
        System.out.println("✓ Student test status: " + status);
        
        boolean hasIcon = solutionResultsPO.hasPassedIcon(studentTest) || 
                          solutionResultsPO.hasFailedIcon(studentTest);
        assertTrue(hasIcon, "Visual indicator should be displayed for student test");
        System.out.println("✓ Visual indicator displayed for student test");
    }

    @Test
    @Order(7)
    @DisplayName("Return to home button works")
    public void testReturnToHomeButton() throws InterruptedException {
        assertTrue(solutionResultsPO.isReturnHomeButtonVisible(), 
            "Return to home button should be visible");
        
        solutionResultsPO.clickReturnHomeButton();
        Thread.sleep(1000);
        
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        wait.until(ExpectedConditions.urlContains("/"));
        
        String currentUrl = driver.getCurrentUrl();
        assertTrue(currentUrl.endsWith("/") || currentUrl.contains("/home"), 
            "Should navigate to home page");
        System.out.println("✓ Successfully navigated to home");
    }
}
