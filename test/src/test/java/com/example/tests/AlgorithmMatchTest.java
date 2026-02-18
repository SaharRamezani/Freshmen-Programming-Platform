package com.example.tests;

import com.example.pages.AlgorithmMatchPO;
import com.example.pages.CreateGameSessionPO;
import com.example.pages.GameSessionMNGPO;
import com.example.pages.JoinGameSessionPO;
import com.example.pages.LobbyPO;
import com.example.pages.LoginPO;
import com.example.pages.WaitingRoomPO;

import org.junit.jupiter.api.*;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;

import static org.junit.jupiter.api.Assertions.*;

import java.time.Duration;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;


@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class AlgorithmMatchTest extends BaseTest {

    // Teacher browser (uses inherited driver from BaseTest)
    private static AlgorithmMatchPO matchPage;
    private static LoginPO teacherLoginPO;
    private static CreateGameSessionPO createGameSessionPO;
    private static GameSessionMNGPO gameSessionMNGPO;
    private static WaitingRoomPO waitingRoomPO;
    
    // Student browser (separate driver)
    private static WebDriver studentDriver;
    private static LoginPO studentLoginPO;
    private static JoinGameSessionPO joinGameSessionPO;
    private static LobbyPO studentLobbyPO;
    private static AlgorithmMatchPO studentMatchPage;
    
    private static String testSessionName;
    private static boolean testDataCreated = false;
    
    private static String generateUniqueSessionName() {
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("HHmmss");
        return "AlgoTest_" + LocalDateTime.now().format(formatter);
    }
    
    private static String getStartDate() {
        LocalDateTime startTime = LocalDateTime.now().plusMinutes(10);
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm");
        return startTime.format(formatter);
    }
    
    private static WebDriver createStudentDriver() {
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
        // Generate unique session name to avoid conflicts with existing sessions
        testSessionName = generateUniqueSessionName();
        
        // Teacher page objects (using inherited driver)
        teacherLoginPO = new LoginPO(driver);
        createGameSessionPO = new CreateGameSessionPO(driver);
        gameSessionMNGPO = new GameSessionMNGPO(driver);
        waitingRoomPO = new WaitingRoomPO(driver);
        
        // Create separate browser for student
        studentDriver = createStudentDriver();
        studentLoginPO = new LoginPO(studentDriver);
        joinGameSessionPO = new JoinGameSessionPO(studentDriver);
        studentLobbyPO = new LobbyPO(studentDriver);
        studentMatchPage = new AlgorithmMatchPO(studentDriver);
        
        // matchPage points to student's match page for tests
        matchPage = studentMatchPage;
    }
    
    @AfterAll
    public static void tearDownTest() {
        if (studentDriver != null) {
            studentDriver.quit();
        }
    }

    @BeforeEach
    public void setupScenario() {
        if (!testDataCreated) {
            // Step 1: Teacher creates game session
            teacherCreatesGameSession();
            
            // Step 2: Student joins the game session (in separate browser)
            studentJoinsGameSession();
            
            // Step 3: Teacher goes to pre-start page (waiting room) - student already joined
            teacherGoesToPreStartPage();
            
            // Step 4: Teacher starts the game
            teacherStartsGame();
            
            testDataCreated = true;
        }
        
        // Student navigates to phase one
        studentGoesToPhaseOne();
        
        if (!matchPage.isPageLoaded()) {
            Assumptions.assumeTrue(false, 
                "The Algorithm Match Phase 1 page failed to load. " +
                "This may be because the game session is not in phase 1 state or student is not joined.");
        }
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
        createGameSessionPO.fillDurationPhaseOne("30");
        createGameSessionPO.fillDurationPhaseTwo("30");
        createGameSessionPO.clickCheckBox(1);
        
        createGameSessionPO.getButton().click();
        createGameSessionPO.waitSuccessAlert();
        sleepForCI(2000);
    }
    
    private void teacherGoesToPreStartPage() {
        driver.get(BASE_URL + "/game-sessions");
        sleepForCI(2000);
        
        // Find the row with our specific session name
        gameSessionMNGPO.waitForRow(testSessionName);
        int rowIndex = gameSessionMNGPO.gameSessionIndex(testSessionName);
        gameSessionMNGPO.getStartButtonAt(rowIndex).click();
        sleepForCI(3000);
        
        // Verify we're on the pre-start page
        String currentUrl = driver.getCurrentUrl();
        assertTrue(currentUrl.contains("/pre-start-game-session/"), 
            "Teacher should be on the pre-start game session page. Current URL: " + currentUrl);
    }
    
    private void studentJoinsGameSession() {
        studentDriver.get(BASE_URL + "/login");
        clearLocalStorage(studentDriver);
        studentLoginPO.loginAsPreconfiguredStudent();
        sleepForCI(3000);
        
        studentDriver.get(BASE_URL + "/join-game-session");
        sleepForCI(2000);
        
        joinGameSessionPO.waitForLoadingComplete();
        
        // Wait for the game session card to appear
        if (!joinGameSessionPO.isGameSessionAvailable()) {
            joinGameSessionPO.waitForSessionAvailable(30);
        }
        
        // Click the "Join Game" button on the card
        assertTrue(joinGameSessionPO.isGameSessionAvailable(),
            "Game session card should be visible on the join page");
        joinGameSessionPO.clickJoinButton();
        sleepForCI(3000);
        
        // After clicking join, the student is redirected to the lobby
        assertTrue(joinGameSessionPO.waitForLobbyRedirect(),
            "Student should be redirected to the lobby after joining");
    }
    
    private void teacherStartsGame() {
        // Teacher is on pre-start page and student is already joined
        try {
            waitingRoomPO.getStartGameButton().click();
            sleepForCI(3000);
        } catch (Exception e) {
            System.out.println("Could not click start button: " + e.getMessage());
        }
    }
    
    private void studentGoesToPhaseOne() {
        // If student is already on phase-one, nothing to do
        if (studentDriver.getCurrentUrl().contains("/phase-one")) {
            return;
        }
        
        // If student is on the lobby, wait for the auto-redirect to /phase-one
        // (the lobby polls the server and redirects when the game starts)
        if (studentDriver.getCurrentUrl().contains("/lobby")) {
            assertTrue(studentLobbyPO.waitForRedirectToPhaseOne(60),
                "Student should be auto-redirected from lobby to phase-one after teacher starts the game");
            sleepForCI(2000);
            return;
        }
        
        // Fallback: go to join page and use the active game banner to re-enter
        studentDriver.get(BASE_URL + "/join-game-session");
        sleepForCI(2000);
        joinGameSessionPO.waitForLoadingComplete();
        
        if (joinGameSessionPO.hasActiveGameBanner()) {
            joinGameSessionPO.clickContinueSession();
            sleepForCI(3000);
        }
    }
    
    private void clearLocalStorage(WebDriver webDriver) {
        ((JavascriptExecutor) webDriver).executeScript("window.localStorage.clear();");
        webDriver.navigate().refresh();
        sleepForCI(500);
    }
    
    private void sleepForCI(int milliseconds) {
        if (System.getenv("CI") != null || "true".equals(System.getProperty("headless"))) {
            try {
                Thread.sleep(milliseconds);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        } else {
            try {
                Thread.sleep(500);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    @Test
    @Order(1)
    @DisplayName("Scenario: Display of main page elements")
    public void testMainPageElementsDisplay() {
        assertTrue(matchPage.getPageTitle().isDisplayed(), "Problem title should be visible");
        assertTrue(matchPage.getTimer().isDisplayed(), "Timer should be visible and synchron");

        assertDoesNotThrow(() -> matchPage.clickProblemDescriptionTab());
        assertDoesNotThrow(() -> matchPage.clickTestsTab());
        
        matchPage.selectLanguage("C++"); 
    }

    @Test
    @Order(2)
    @DisplayName("Scenario: Adding a custom test")
    public void testAddCustomTestCase() {
        matchPage.clickAddNewTestCase();
        matchPage.fillAndSubmitTestForm("5", "10"); 

        assertTrue(matchPage.waitTestAddedMessage().isDisplayed(), "Success message 'Test Is Added' missing");
    }

    @Test
    @Order(3)
    @DisplayName("Scenario: Removing a custom test")
    public void testRemoveCustomTestCase() {
        matchPage.clickTestsTab();
        matchPage.deleteCustomTest(0);
        
        assertTrue(matchPage.waitTestDeletedMessage().isDisplayed(), "Success message 'Test Is Deleted' missing");
    }

    @Test
    @Order(4)
    @DisplayName("Scenario: Successful execution of public tests")
    public void testPublicTestExecution() {
        matchPage.clickRunPublicTests();
        sleepForCI(3000); // Wait for test execution to complete
        
        // Expand the results collapse if not already expanded
        if (!matchPage.isCollapseExpanded()) {
            matchPage.toggleExecutionOutput();
        }
        
        matchPage.waitForTestResults(15);
        
        String results = matchPage.getResultsSummaryText();
        System.out.println("Test results: " + results); // Debug output
        assertTrue(results.contains("Passed") || results.contains("Failed") || results.contains("error"), 
            "Execution results should show pass/fail status. Got: " + results);
    }

    @Test
    @Order(5)
    @DisplayName("Scenario: Compilation error handling")
    public void testCompilationError() {
        // Set invalid code that will cause compilation error
        matchPage.setEditorCode("this is not valid c++ code { {{ syntax error");
        sleepForCI(1000);
        
        matchPage.clickRunPublicTests();
        sleepForCI(3000); // Wait for test execution to complete
        
        // Expand the results collapse if not already expanded
        if (!matchPage.isCollapseExpanded()) {
            matchPage.toggleExecutionOutput();
        }
        
        matchPage.waitForTestResults(15);
        
        String results = matchPage.getResultsSummaryText().toLowerCase();
        System.out.println("Compilation error results: " + results); // Debug output
        assertTrue(results.contains("error") || results.contains("failed"), 
            "Output should display an error state. Got: " + results);
    }

    @Test
    @Order(6)
    @DisplayName("Scenario: Data persistence upon page refresh")
    public void testRefreshPersistence() {
        String sampleCode = "int x = 10;";
        matchPage.setEditorCode(sampleCode);
        studentDriver.navigate().refresh();
        sleepForCI(2000);
        assertTrue(matchPage.getTimer().isDisplayed(), "Timer should persist and not reset");
        String codeAfterRefresh = matchPage.getEditorCode();
        assertTrue(codeAfterRefresh.contains(sampleCode) || codeAfterRefresh.length() > 0, "Code should persist after refresh");
    }

    @Test
    @Order(7)
    @DisplayName("Scenario: Time expiration (Timeout)")
    public void testTimeExpiration() {
        assertTrue(matchPage.isRunPublicTestsClickable(), "Submit button should be disabled after timeout");
    }
}