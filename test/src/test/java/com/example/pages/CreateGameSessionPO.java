package com.example.pages;

import org.openqa.selenium.Alert;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;
import java.util.*;

public class CreateGameSessionPO {
    private WebDriver driver;
    private WebDriverWait wait;
    private static final String PAGE_TITLE_XPATH = "//*[@id=\"page_title\"]";
    private static final String ANTD_DIV_TABLE_XPATH = "//*[@id=\"game-session-creation-table\"]";
    private static final String TABLE_BODY_XPATH = ANTD_DIV_TABLE_XPATH + "//tbody[contains(@class,'ant-table-tbody')]";
    private static final String BUTTON_XPATH = "//*[@id=\"create-game-session-button\"]/button";
    private static final String SUCCESS_MESSAGE_XPATH = "//div[contains(@class,'popup-alert')]//div[contains(@class,'alert-content') and text()='The game session has been created successfully!']";
    private static final String WARNING_MESSAGE_XPATH = "//div[contains(@class,'popup-alert')]//div[contains(@class,'alert-content') and text()='Please select at least one match to create a game session']";
    private static final String SESSION_NAME_INPUT_XPATH = "//*[@id=\"session-name\"]";
    private static final String START_DATE_INPUT_XPATH = "//*[@id=\"start-date\"]";
    private static final String CALENDAR_OK_BUTTON_XPATH = "//button[@class='ant-btn css-dev-only-do-not-override-hofb1t ant-btn-primary ant-btn-color-primary ant-btn-variant-solid ant-btn-sm']";
    private static final String DURATION_PHASE_ONE_INPUT_XPATH = "//*[@id=\"duration_phas1\"]";
    private static final String DURATION_PHASE_TWO_INPUT_XPATH = "//*[@id=\"duration_phas2\"]";
    private static final String SEARCH_INPUT_CSS = "input[placeholder='Search matches...']";

    public CreateGameSessionPO(WebDriver driver) {
        this.driver = driver;
        // Use longer timeout in CI environments
        int waitTimeout = (System.getenv("CI") != null || "true".equals(System.getProperty("headless"))) ? 30 : 10;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(waitTimeout));
    }

    public boolean isPageLoaded() {
        try {
            return getPageTitle().isDisplayed() &&
                    getPageTitle().getText().equals("Create Game Session");
        } catch (Exception e) {
            return false;
        }
    }

    public boolean isTablePresent() {
        return driver.findElement(By.tagName("table")).isDisplayed();
    }

    public WebElement getPageTitle() {
        return driver.findElement(By.xpath(PAGE_TITLE_XPATH));
    }

    private WebElement getElementAt(int row, int col) {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath(TABLE_BODY_XPATH + "/tr[" + Integer.toString(row) + "]/td[" + Integer.toString(col) + "]")));
    }

    public List<WebElement> getRows() {
        return wait.until(ExpectedConditions.visibilityOfAllElementsLocatedBy(By.xpath(TABLE_BODY_XPATH + "/tr")));
    }

    public WebElement getCheckBox(int row) {
        // Checkbox is in column 4 (Selected column) based on Ant Design table structure
        return getElementAt(row, 4);
    }
    
    /**
     * Get the checkbox input element for a specific row (1-indexed)
     */
    public WebElement getCheckBoxInput(int row) {
        WebElement checkboxCell = getCheckBox(row);
        return checkboxCell.findElement(By.cssSelector("input.ant-checkbox-input"));
    }
    
    /**
     * Check if the checkbox for a specific row is selected
     */
    public boolean isCheckBoxSelected(int row) {
        WebElement checkboxInput = getCheckBoxInput(row);
        return checkboxInput.isSelected();
    }
    
    /**
     * Click the checkbox for a specific row (1-indexed)
     */
    public void clickCheckBox(int row) {
        WebElement checkboxInput = getCheckBoxInput(row);
        checkboxInput.click();
    }

    public WebElement getButton() {
        return driver.findElement(By.xpath(BUTTON_XPATH));
    }

    public WebElement waitSuccessAlert() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(
                By.xpath(SUCCESS_MESSAGE_XPATH)));
    }

    public WebElement waitErrorAlert() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(
                By.xpath(WARNING_MESSAGE_XPATH)));
    }

    public WebElement getSessionNameInput() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath(SESSION_NAME_INPUT_XPATH)));
    }

    public WebElement getStartDateInput() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath(START_DATE_INPUT_XPATH)));
    }

    public void fillSessionName(String sessionName) {
        WebElement sessionNameInput = getSessionNameInput();
        sessionNameInput.clear();
        sessionNameInput.sendKeys(sessionName);
    }

    public void fillStartDate(String startDate) {
        WebElement startDateInput = getStartDateInput();
        startDateInput.clear();
        startDateInput.sendKeys(startDate);

        WebElement okButton = wait.until(ExpectedConditions.elementToBeClickable(By.xpath(CALENDAR_OK_BUTTON_XPATH)));
        okButton.click();
    }

    public void fillDurationPhaseOne(String duration) {
        WebElement durationPhaseOneInput = wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath(DURATION_PHASE_ONE_INPUT_XPATH)));
        durationPhaseOneInput.clear();
        durationPhaseOneInput.sendKeys(duration);
    }

    public void fillDurationPhaseTwo(String duration) {
        WebElement durationPhaseTwoInput = wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath(DURATION_PHASE_TWO_INPUT_XPATH)));
        durationPhaseTwoInput.clear();
        durationPhaseTwoInput.sendKeys(duration);
    }

    public void searchMatch(String query) {
        WebElement searchInput = wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector(SEARCH_INPUT_CSS)));
        searchInput.clear();
        searchInput.sendKeys(query);
    }

    public String getMatchNameAt(int row) {
        WebElement nameCell = getElementAt(row, 1);
        return nameCell.getText();
    }
}
