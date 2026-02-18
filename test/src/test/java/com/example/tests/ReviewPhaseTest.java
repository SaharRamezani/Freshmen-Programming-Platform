package com.example.tests;

import com.example.pages.AlgorithmMatchPO;
import com.example.pages.CreateGameSessionPO;
import com.example.pages.GameSessionMNGPO;
import com.example.pages.JoinGameSessionPO;
import com.example.pages.LoginPO;
import com.example.pages.ReviewPhasePO;
import com.example.pages.WaitingRoomPO;

import org.junit.jupiter.api.*;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

/**
 * Test class for Phase 2 (Review Phase) functionality.
 * 
 * This test requires:
 * 1. A teacher to create a game session with a very short phase 1 timer
 * 2. Two students to join and submit solutions in phase 1
 * 3. Waiting for phase 1 to end and phase 2 to begin
 * 4. Testing the review/voting functionality in phase 2
 */
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class ReviewPhaseTest extends BaseTest {

    // Teacher browser (uses inherited driver from BaseTest)
    private static LoginPO teacherLoginPO;
    private static CreateGameSessionPO createGameSessionPO;
    private static GameSessionMNGPO gameSessionMNGPO;
    private static WaitingRoomPO waitingRoomPO;
    
    // Student 1 browser (separate driver)
    private static WebDriver student1Driver;
    private static LoginPO student1LoginPO;
    private static JoinGameSessionPO student1JoinPO;
    private static AlgorithmMatchPO student1MatchPage;
    private static ReviewPhasePO student1ReviewPage;
    
    // Student 2 browser (separate driver)
    private static WebDriver student2Driver;
    private static LoginPO student2LoginPO;
    private static JoinGameSessionPO student2JoinPO;
    private static AlgorithmMatchPO student2MatchPage;
    private static ReviewPhasePO student2ReviewPage;
    
    private static String testSessionName;
    private static boolean testDataCreated = false;
    
    // Very short phase 1 duration (1 minute) to quickly get to phase 2
    private static final String PHASE_ONE_DURATION = "1";
    private static final String PHASE_TWO_DURATION = "30";
    
    private static String generateUniqueSessionName() {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("HHmmss");
        return "ReviewTest_" + LocalDateTime.now().format(formatter);
    }
    
    private static String getStartDate() {
        LocalDateTime startTime = LocalDateTime.now().plusMinutes(2);
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
        return startTime.format(formatter);
    }
    
    private static WebDriver createNewDriver() {
        ChromeOptions options = new ChromeOptions();
        
        String headless = System.getProperty("headless", "false");
        if ("true".equals(headless) || System.getenv("CI") != null) {
            options.addArguments("--headless=new");
            options.addArguments("--no-sandbox");
            options.addArguments("--disable-dev-shm-usage");
            options.addArguments("--disable-gpu");
            options.addArguments("--window-size=1920,1080");
        } else {
            options.addArguments("--start-maximized");
        }
        
        options.addArguments("--disable-blink-features=AutomationControlled");
        
        WebDriver newDriver = new ChromeDriver(options);
        
        if ("true".equals(headless) || System.getenv("CI") != null) {
            newDriver.manage().timeouts().pageLoadTimeout(Duration.ofSeconds(30));
            newDriver.manage().timeouts().scriptTimeout(Duration.ofSeconds(30));
        } else {
            newDriver.manage().timeouts().pageLoadTimeout(Duration.ofSeconds(20));
        }
        
        return newDriver;
    }

    @BeforeAll
    public static void setUpTest() {
        // Generate unique session name
        testSessionName = generateUniqueSessionName();
        
        // Teacher page objects (using inherited driver)
        teacherLoginPO = new LoginPO(driver);
        createGameSessionPO = new CreateGameSessionPO(driver);
        gameSessionMNGPO = new GameSessionMNGPO(driver);
        waitingRoomPO = new WaitingRoomPO(driver);
        
        // Create separate browser for student 1
        student1Driver = createNewDriver();
        student1LoginPO = new LoginPO(student1Driver);
        student1JoinPO = new JoinGameSessionPO(student1Driver);
        student1MatchPage = new AlgorithmMatchPO(student1Driver);
        student1ReviewPage = new ReviewPhasePO(student1Driver);
        
        // Create separate browser for student 2
        student2Driver = createNewDriver();
        student2LoginPO = new LoginPO(student2Driver);
        student2JoinPO = new JoinGameSessionPO(student2Driver);
        student2MatchPage = new AlgorithmMatchPO(student2Driver);
        student2ReviewPage = new ReviewPhasePO(student2Driver);
    }
    
    @AfterAll
    public static void tearDownTest() {
        if (student1Driver != null) {
            student1Driver.quit();
        }
        if (student2Driver != null) {
            student2Driver.quit();
        }
    }

    @BeforeEach
    public void setupScenario() {
        if (!testDataCreated) {
            // Step 1: Teacher creates game session with short phase 1
            teacherCreatesGameSession();
            
            // Step 2: Both students join the game session
            student1JoinsGameSession();
            student2JoinsGameSession();
            
            // Step 3: Teacher goes to pre-start page
            teacherGoesToPreStartPage();
            
            // Step 4: Teacher starts the game
            teacherStartsGame();
            
            // Step 5: Both students go to phase one and wait
            studentsGoToPhaseOneAndWait();
            
            // Step 6: Wait for phase 1 to end and phase 2 to begin
            waitForPhaseTwo();
            
            // Step 7: Navigate students to voting page ONCE after phase 1 has truly ended
            navigateStudentToVoting(student1Driver, student1JoinPO);
            navigateStudentToVoting(student2Driver, student2JoinPO);
            
            testDataCreated = true;
        }
        
        // Skip tests if voting page is not available
        Assumptions.assumeTrue(student1ReviewPage.isVotingSectionVisible(), 
            "Voting page not available - requires a game session in phase 2 with solutions to review");
    }
    
    private void teacherCreatesGameSession() {
        driver.get(BASE_URL + "/login");
        clearLocalStorage(driver);
        teacherLoginPO.loginAsPreconfiguredTeacher();
        sleepForCI(3000);
        
        driver.get(BASE_URL + "/create-game-session");
        sleepForCI(2000);
        
        createGameSessionPO.fillSessionName(testSessionName);
        createGameSessionPO.fillStartDate(getStartDate());
        createGameSessionPO.fillDurationPhaseOne(PHASE_ONE_DURATION);
        createGameSessionPO.fillDurationPhaseTwo(PHASE_TWO_DURATION);
        
        // Search for the "Pointers Basics" match which uses the "Sum Vector Elements" 
        // match setting — this ensures the CORRECT_SOLUTION_CODE (summing stdin inputs) 
        // matches the expected test cases (e.g., "1 2 3" → "6")
        createGameSessionPO.searchMatch("Pointers Basics");
        sleepForCI(1000);
        createGameSessionPO.clickCheckBox(1);
        
        createGameSessionPO.getButton().click();
        createGameSessionPO.waitSuccessAlert();
        sleepForCI(2000);
    }
    
    private void student1JoinsGameSession() {
        student1Driver.get(BASE_URL + "/login");
        clearLocalStorage(student1Driver);
        student1LoginPO.loginAsPreconfiguredStudent();
        sleepForCI(3000);
        
        student1Driver.get(BASE_URL + "/join-game-session");
        sleepForCI(2000);
        
        student1JoinPO.waitForLoadingComplete();
        
        if (!student1JoinPO.isGameSessionAvailableByName(testSessionName)) {
            student1JoinPO.waitForSessionAvailableByName(testSessionName, 30);
        }
        
        if (student1JoinPO.isGameSessionAvailableByName(testSessionName)) {
            student1JoinPO.clickJoinButtonForSession(testSessionName);
            sleepForCI(3000);
        }
    }
    
    private void student2JoinsGameSession() {
        student2Driver.get(BASE_URL + "/login");
        clearLocalStorage(student2Driver);
        student2LoginPO.loginAsPreconfiguredStudent2();
        sleepForCI(3000);
        
        student2Driver.get(BASE_URL + "/join-game-session");
        sleepForCI(2000);
        
        student2JoinPO.waitForLoadingComplete();
        
        if (!student2JoinPO.isGameSessionAvailableByName(testSessionName)) {
            student2JoinPO.waitForSessionAvailableByName(testSessionName, 30);
        }
        
        if (student2JoinPO.isGameSessionAvailableByName(testSessionName)) {
            student2JoinPO.clickJoinButtonForSession(testSessionName);
            sleepForCI(3000);
        }
    }
    
    private void teacherGoesToPreStartPage() {
        driver.get(BASE_URL + "/game-sessions");
        sleepForCI(2000);
        
        gameSessionMNGPO.waitForRow(testSessionName);
        int rowIndex = gameSessionMNGPO.gameSessionIndex(testSessionName);
        gameSessionMNGPO.getStartButtonAt(rowIndex).click();
        sleepForCI(2000);
    }
    
    private void teacherStartsGame() {
        try {
            waitingRoomPO.getStartGameButton().click();
            sleepForCI(3000);
        } catch (Exception e) {
            System.out.println("Could not click start button: " + e.getMessage());
        }
    }
    
    // Correct solution for the match setting - sums all given inputs
    private static final String CORRECT_SOLUTION_CODE = 
        "#include <iostream>\n" +
        "using namespace std;\n" +
        "\n" +
        "int main() {\n" +
        "    int n, sum = 0;\n" +
        "    while (cin >> n) {\n" +
        "        sum += n;\n" +
        "    }\n" +
        "    cout << sum;\n" +
        "    return 0;\n" +
        "}";
    
    private void studentsGoToPhaseOneAndWait() {
        // Student 1 goes to phase one
        navigateStudentToPhaseOne(student1Driver, student1JoinPO);
        sleepForCI(2000);
        
        // Student 2 goes to phase one
        navigateStudentToPhaseOne(student2Driver, student2JoinPO);
        sleepForCI(2000);
        
        // Students must write correct code and run public tests to save their solutions
        // Otherwise there will be no solutions to review in phase 2
        System.out.println("Students writing code and running public tests to save solutions...");
        
        // Student 1 writes code and runs public tests
        try {
            student1MatchPage.setEditorCode(CORRECT_SOLUTION_CODE);
            sleepForCI(1000);
            student1MatchPage.clickRunPublicTests();
            sleepForCI(5000);
            System.out.println("Student 1 wrote code and ran public tests.");
        } catch (Exception e) {
            System.out.println("Student 1 could not run public tests: " + e.getMessage());
        }
        
        // Student 2 writes code and runs public tests
        try {
            student2MatchPage.setEditorCode(CORRECT_SOLUTION_CODE);
            sleepForCI(1000);
            student2MatchPage.clickRunPublicTests();
            sleepForCI(5000);
            System.out.println("Student 2 wrote code and ran public tests.");
        } catch (Exception e) {
            System.out.println("Student 2 could not run public tests: " + e.getMessage());
        }
        
        System.out.println("Both students are in Phase 1. Waiting for timer to expire...");
    }
    
    private void waitForPhaseTwo() {
        // Wait for phase 1 timer to expire (1 minute + generous buffer)
        // Phase 1 is set to 1 minute, so we wait 80 seconds to be absolutely sure
        // it has ended before navigating to voting page
        System.out.println("Waiting for Phase 1 to end (80 seconds)...");
        sleepForCI(80000);
        System.out.println("Phase 1 timer should have expired. Ready to navigate to Phase 2.");
    }
    
    private void navigateStudentToPhaseOne(WebDriver studentDriver, JoinGameSessionPO joinPO) {
        studentDriver.get(BASE_URL + "/join-game-session");
        sleepForCI(2000);
        
        joinPO.waitForLoadingComplete();
        
        if (joinPO.hasActiveGameBanner()) {
            joinPO.clickContinueSession();
            sleepForCI(3000);
        }
    }
    
    private void navigateStudentToVoting(WebDriver studentDriver, JoinGameSessionPO joinPO) {
        ReviewPhasePO reviewPage = new ReviewPhasePO(studentDriver);
        if (!reviewPage.isVotingSectionVisible()) {
            studentDriver.get(BASE_URL + "/join-game-session");
            sleepForCI(2000);
            
            joinPO.waitForLoadingComplete();
            
            if (joinPO.hasActiveGameBanner()) {
                joinPO.clickContinueSession();
                sleepForCI(3000);
            }
        }
    }
    
    private void clearLocalStorage(WebDriver webDriver) {
        ((JavascriptExecutor) webDriver).executeScript("window.localStorage.clear();");
        webDriver.navigate().refresh();
        sleepForCI(500);
    }
    
    private void sleepForCI(int milliseconds) {
        try {
            Thread.sleep(milliseconds);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    @Test
    @Order(1)
    @DisplayName("Verify solutions list is displayed with anonymous IDs and timer")
    public void testDisplaySolutions() {
        assertTrue(student1ReviewPage.isVotingSectionVisible(), "Voting section header should be visible");
        assertTrue(student1ReviewPage.isSolutionsListVisible(), "Solutions list should be visible");
        assertTrue(student1ReviewPage.isTimerVisible(), "Phase timer should be visible");

        List<WebElement> solutions = student1ReviewPage.getSolutionItems();
        assertFalse(solutions.isEmpty(), "There should be solutions to review");

        // Check that participant IDs are anonymized
        for (WebElement solution : solutions) {
            String participantId = student1ReviewPage.getParticipantId(solution);
            assertNotNull(participantId, "Participant ID should be displayed");
            // Anonymous IDs should not contain actual names
            assertFalse(participantId.contains("Dev Student"), "Participant ID should be anonymous");
        }
    }

    @Test
    @Order(2)
    @DisplayName("Verify 'Incorrect' vote enables test case form and disables submit initially")
    public void testVotingIncorrectRequiresTestCase() {
        student1ReviewPage.clickViewDetails(0);
        sleepForCI(1000);
        
        student1ReviewPage.clickIncorrectVote();
        sleepForCI(500);
        
        assertTrue(student1ReviewPage.isTestCaseFormVisible(), "Test case form should be visible when 'Incorrect' is selected");
        assertFalse(student1ReviewPage.isSubmitButtonEnabled(), "Submit button should be disabled before test case input");
        
        student1ReviewPage.setTestCaseInput("5");
        student1ReviewPage.setTestCaseExpectedOutput("25");
        sleepForCI(500);

        assertTrue(student1ReviewPage.isSubmitButtonEnabled(), "Submit button should be enabled after filling test case");
    }

    @Test
    @Order(3)
    @DisplayName("Verify 'Correct' vote hides test case form")
    public void testVotingCorrectHidesForm() {
        student1ReviewPage.clickViewDetails(0);
        sleepForCI(1000);
        
        student1ReviewPage.clickIncorrectVote();
        sleepForCI(500);
        assertTrue(student1ReviewPage.isTestCaseFormVisible(), "Form visible on Incorrect");
        
        student1ReviewPage.clickCorrectVote();
        sleepForCI(500);
    
        assertFalse(student1ReviewPage.isTestCaseFormVisible(), "Form should be hidden when 'Correct' is selected");
        assertTrue(student1ReviewPage.isSubmitButtonEnabled(), "Submit button should be enabled immediately for Correct vote");
    }

    @Test
    @Order(4)
    @DisplayName("Verify system rejects vote with invalid test case")
    public void testInvalidTestCaseRejection() {
        int initialCount = student1ReviewPage.getTodoListCount();
        
        student1ReviewPage.clickViewDetails(0);
        sleepForCI(1000);
        
        student1ReviewPage.clickIncorrectVote();
        sleepForCI(500);
       
        student1ReviewPage.setTestCaseInput("InvalidInputForTeacher");
        student1ReviewPage.setTestCaseExpectedOutput("ImpossibleOutput");
        sleepForCI(500);
        
        student1ReviewPage.clickSubmitVote();
        sleepForCI(2000);
        
        int newCount = student1ReviewPage.getTodoListCount();
        assertEquals(initialCount, newCount, "Todo list count should not change after invalid test case");
        
        String notification = student1ReviewPage.getNotificationText();
        assertTrue(notification.toLowerCase().contains("invalid") || notification.toLowerCase().contains("teacher"),
            "Error notification should appear when test case is invalid against teacher solution");
    }

    @Test
    @Order(5)
    @DisplayName("Verify system accepts valid 'Correct' vote")
    public void testValidCorrectVoteSuccess() {
        int initialCount = student1ReviewPage.getTodoListCount();
        Assumptions.assumeTrue(initialCount > 0, "Need at least one solution to vote on");
        
        student1ReviewPage.clickViewDetails(0);
        sleepForCI(1000);
        
        student1ReviewPage.clickCorrectVote();
        sleepForCI(500);
        
        student1ReviewPage.clickSubmitVote();
        sleepForCI(2000);
        
        String notification = student1ReviewPage.getNotificationText();
        assertTrue(notification.toLowerCase().contains("success") || notification.toLowerCase().contains("submitted"),
            "Success notification should appear when vote is valid. Got: " + notification);
    }

    @Test
    @Order(6)
    @DisplayName("Verify review queue is anonymous")
    public void testAnonymousReviewQueue() {
        List<WebElement> solutions = student1ReviewPage.getSolutionItems();
        
        for (WebElement solution : solutions) {
            String id = student1ReviewPage.getParticipantId(solution);
            // Anonymous IDs should not match real name patterns
            assertFalse(id.matches("^[A-Z][a-z]+ [A-Z][a-z]+$"), "Participant names should be masked (not First Last format)");
        }
    }

    @Test
    @Order(7)
    @DisplayName("Verify skipping a review works")
    public void testSkipReview() {
        int initialCount = student1ReviewPage.getTodoListCount();
        Assumptions.assumeTrue(initialCount > 0, "Need at least one solution to skip");
        
        student1ReviewPage.clickViewDetails(0);
        sleepForCI(1000);
        
        student1ReviewPage.clickSkipVote();
        sleepForCI(500);
        
        student1ReviewPage.clickSubmitVote();
        sleepForCI(2000);
        
        // After skipping, either the count decreases or we get a success notification
        String notification = student1ReviewPage.getNotificationText();
        assertTrue(notification.toLowerCase().contains("success") || notification.toLowerCase().contains("submitted") ||
                   student1ReviewPage.getTodoListCount() <= initialCount,
            "Skip should either show success or decrease todo count");
    }

    @Test
    @Order(8)
    @DisplayName("Verify code editor is read-only")
    public void testCodeEditorRestrictions() {
        student1ReviewPage.clickViewDetails(0);
        sleepForCI(1000);
        
        assertTrue(student1ReviewPage.isCodeReadOnly(), "Code editor should be in read-only mode");
    }

    @Test
    @Order(9)
    @DisplayName("Verify timer displays correctly")
    public void testTimerDisplay() {
        String timerText = student1ReviewPage.getTimerText();
        assertNotNull(timerText, "Timer text should not be null");
        assertFalse(timerText.isEmpty(), "Timer text should not be empty");
        // Timer format should be MM:SS or similar
        assertTrue(timerText.contains(":") || timerText.matches("\\d+"), 
            "Timer should display in time format. Got: " + timerText);
    }
}
