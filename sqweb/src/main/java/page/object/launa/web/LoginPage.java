package page.object.launa.web;

import entity.LoginInfo;
import org.openqa.selenium.WebDriver;

import java.util.List;

/**
 * @author yuxiangfeng
 */
public interface LoginPage {

    /**
     * 登录
     * @param driver
     * @return
     */
    WebDriver login(WebDriver driver);

    /**
     * 获取用户List
     * @return
     */
    List<LoginInfo> helpGetUserList();

    /**
     * 登出
     * @param driver
     * @return
     */
    boolean logout(WebDriver driver);

    /**
     * 登录
     * @param driver
     * @param mobile
     * @param password
     * @return
     */
    boolean loginByMobileAndPassword(WebDriver driver, String mobile, String password);
}
