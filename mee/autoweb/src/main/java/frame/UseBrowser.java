package frame;

import org.openqa.selenium.WebDriver;

/**
 * @author fengyuxiang
 */
public interface UseBrowser {
    String FIREFOX="firefox";
    String CHROME="chrome";

    /**
     * 使用浏览器
     * @param driverType
     * @return
     */
    WebDriver useBrowser(String driverType);

    /**
     * 选择Chrome浏览器
     * @return
     */
    WebDriver useChrome();

    /**
     *选择Chrome浏览器
     * @param fresh 全新的，没有旧缓存的
     * @return
     */
    WebDriver useChrome(boolean fresh);

    /**
     * 选择Firefox浏览器
     * @return
     */
    WebDriver useFirefox();

    /**
     *选择Firefox浏览器
     * @param fresh 全新的，没有旧缓存的
     * @return
     */
    WebDriver useFirefox(boolean fresh);

}
