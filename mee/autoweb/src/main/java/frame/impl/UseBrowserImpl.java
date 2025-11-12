package frame.impl;

import frame.TimeoutUtil;
import frame.UseBrowser;
import io.github.bonigarcia.wdm.WebDriverManager;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.firefox.FirefoxDriver;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.concurrent.Callable;


/**
 * @author fengyuxiang
 */
@Component
public class UseBrowserImpl implements UseBrowser {

    private static final String CHROME_DRIVER_PATH_KEY = "webdriver.chrome.driver";
    private static final String FIREFOX_DRIVER_PATH_KEY = "webdriver.gecko.driver";

    @Value("${browserCacheDir:browserCache}")
    String browserCacheDir;
    @Value("${useFreshBrowser:false}")
    boolean useFreshBrowser;
    @Value("${server.run:false}")
    boolean isServerRun;

    @Override
    public WebDriver useBrowser(String driverType){
        if(driverType.equalsIgnoreCase(FIREFOX)){
            return useFirefox();
        }
        if(driverType.equalsIgnoreCase(CHROME)){
            return useChrome();
        }
        throw new RuntimeException("Unsupported browser type:" + driverType);
    }

    @Override
    public WebDriver useChrome(){
        return useChrome(useFreshBrowser);
    }

    public WebDriver useChromeNoPic(){
        newDriver(CHROME_DRIVER_PATH_KEY);
        ChromeOptions options = new ChromeOptions();
        options.addArguments("blink-settings=imagesEnabled=false");
        return new ChromeDriver(options);
    }

    @Override
    public WebDriver useChrome(boolean fresh) {
        newDriver(CHROME_DRIVER_PATH_KEY);
        if (!fresh || isServerRun){
            ChromeOptions options = new ChromeOptions();
            if(!fresh) {
                options.addArguments("--disk-cache-dir=" + browserCacheDir);
            }
            if (isServerRun){
                options.addArguments("--no-sandbox");
                options.addArguments("--disable-dev-shm-usage");
                options.addArguments("--headless");
            }
            return useChromeDriver(options);
        }
        return useChromeDriver();
    }

    private WebDriver useChromeDriver(ChromeOptions options){
        Callable<WebDriver> call = new Callable<WebDriver>() {
            @Override
            public WebDriver call() throws Exception {
                return new ChromeDriver(options);
            }
        };
        WebDriver driver = TimeoutUtil.process(call,30L,1);
        return driver;
    }

    private WebDriver useChromeDriver(){
        Callable<WebDriver> call = new Callable<WebDriver>() {
            @Override
            public WebDriver call() throws Exception {
                return new ChromeDriver();
            }
        };
        WebDriver driver = TimeoutUtil.process(call,30L,1);
        return driver;
    }

    @Override
    public WebDriver useFirefox(){
        return useFirefox(true);
    }

    @Override
    public WebDriver useFirefox(boolean fresh) {
        newDriver(FIREFOX_DRIVER_PATH_KEY);
        return new FirefoxDriver();
    }

    private void newDriver(String driverPathKey){

        WebDriverManager driverManager;
        if (CHROME_DRIVER_PATH_KEY.equals(driverPathKey) && System.getProperty(CHROME_DRIVER_PATH_KEY) == null){
            driverManager = WebDriverManager.chromedriver();
            driverManager.useMirror();
            driverManager.setup();
            return;
        }

        if (FIREFOX_DRIVER_PATH_KEY.equals(driverPathKey) && System.getProperty(FIREFOX_DRIVER_PATH_KEY) == null){
            driverManager = WebDriverManager.firefoxdriver();
            driverManager.useMirror();
            driverManager.setup();
            return;
        }

        throw new IllegalArgumentException("unsupported browser: " + driverPathKey);
    }


}
