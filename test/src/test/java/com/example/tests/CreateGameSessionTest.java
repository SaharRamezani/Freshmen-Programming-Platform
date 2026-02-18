package com.example.tests;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;

import org.junit.jupiter.api.TestMethodOrder;
import org.junit.jupiter.api.MethodOrderer;
import com.example.pages.CreateGameSessionPO;
import com.example.pages.LoginPO;

@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class CreateGameSessionTest extends BaseTest  {
    private static CreateGameSessionPO createGameSessionPage;
    private static LoginPO loginPO;

    @BeforeAll
    public static void setUpTest() {
        // BaseTest.setUp() is automatically called by JUnit due to @BeforeAll in parent class
        // Initialize Page Object here
        loginPO = new LoginPO(driver);
        createGameSessionPage = new CreateGameSessionPO(driver);
    }
    
    @BeforeEach
    public void navigateToPage() {
        navigateTo("/login");
        ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("window.localStorage.clear();");
        driver.navigate().refresh();
        loginPO.loginAsPreconfiguredTeacher();
        
        // Give extra time for page to load in CI environments
        if (System.getenv("CI") != null || "true".equals(System.getProperty("headless"))) {
            try {
                Thread.sleep(3000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
        
        // Navigate to the create game session page before each test
        navigateTo("/create-game-session");
    }

    @Test
    @Order(1)
    @DisplayName("Verify page loads successfully")
    public void testCorrectPageLoads() {
        assertTrue((createGameSessionPage.isPageLoaded() && createGameSessionPage.getPageTitle().getText().equals("Create Game Session") )
        , "Create Game Session page should load successfully");
    }


    @Test
    @Order(2)
    @DisplayName("Verify that table is present")
    public void testTablePresent() {
        assertTrue(createGameSessionPage.isTablePresent(), 
            "Create Game Session page should load successfully");
    }
    
    @Test
    @Order(3)
    @DisplayName("Verify that the game session creates successfully")
    public void testGameSessionCreationSucceed() {
        String sessionName = "Test Session Full";
        String startDate = "2125-12-11 21:09";
        
        createGameSessionPage.fillSessionName(sessionName);
        createGameSessionPage.fillStartDate(startDate);

        createGameSessionPage.fillDurationPhaseOne("10");
        createGameSessionPage.fillDurationPhaseTwo("10");

        // Verify checkboxes are not selected initially
        assertFalse(createGameSessionPage.isCheckBoxSelected(1));
        assertFalse(createGameSessionPage.isCheckBoxSelected(2));
        
        // Click first checkbox and verify state
        createGameSessionPage.clickCheckBox(1);
        assertTrue(createGameSessionPage.isCheckBoxSelected(1));
        assertFalse(createGameSessionPage.isCheckBoxSelected(2));
        
        // Click second checkbox and verify state
        createGameSessionPage.clickCheckBox(2);
        assertTrue(createGameSessionPage.isCheckBoxSelected(2));
        
        createGameSessionPage.getButton().click();

        WebElement alert = createGameSessionPage.waitSuccessAlert();
        
        assertEquals(alert.getText(), "The game session has been created successfully!");
    }

    @Test
    @Order(4)
    @DisplayName("Verify that the game session creation fails without selecting any match")
    public void testGameSessionCreationFails() {
        // Verify checkboxes are not selected initially
        assertFalse(createGameSessionPage.isCheckBoxSelected(1));
        assertFalse(createGameSessionPage.isCheckBoxSelected(2));
        assertFalse(createGameSessionPage.getButton().isEnabled(), "Button should be disabled");
    }
}
