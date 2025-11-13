import frame.UseBrowser;
import org.openqa.selenium.WebDriver;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.test.context.ContextConfiguration;
import org.springframework.test.context.testng.AbstractTestNGSpringContextTests;
import org.testng.Assert;
import org.testng.annotations.Test;
import entity.LoginInfo;
import page.object.launa.web.LoginPage;

@ContextConfiguration(locations = {"classpath:/application-servlet.xml"})
public class LoginAndLogout extends AbstractTestNGSpringContextTests {
    @Autowired
    LoginPage loginPage;
    @Autowired
    UseBrowser useBrowser;

    private boolean loginAndOut(WebDriver driver) {
        LoginInfo loginInfo = loginPage.helpGetUserList().get(0);
        if(loginPage.loginByMobileAndPassword(driver,loginInfo.getMobile(),loginInfo.getPassword())) {
            return loginPage.logout(driver);
        }
        return false;
    }

    /**
     * 登录登出
     */
    @Test
    public void loginAndOut() {
        WebDriver driver = useBrowser.useChrome();
        Assert.assertTrue(loginAndOut(driver));
        driver.quit();
    }

    /**
     * 登录登出，使用全新无旧缓存的浏览器，
     * 可以看到登录后的home页面展示较慢，因为vue单页面应用需要加载较多的js
     */
    @Test
    public void loginAndOut1() {
        WebDriver driver = useBrowser.useChrome(true);
        Assert.assertTrue(loginAndOut(driver));
        driver.quit();
    }


    /**
     * 连续登录登出
     * @throws InterruptedException
     */
    @Test
    public void loginAndOut2() throws InterruptedException {
        WebDriver driver = useBrowser.useChrome();
        Assert.assertTrue(loginAndOut(driver));
        logger.info("====>> finish one!SSSS");
        Thread.sleep(1000);
        Assert.assertTrue(loginAndOut(driver));
        driver.quit();
    }


}
