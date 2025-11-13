package page.object.launa.web;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import ui.UIBase;

import java.util.List;

/**
 * @author yuxiangfeng
 */
public interface BasePage {
    String COMMON="common";
    String SYSTEM="system";
    String FOOTER = "footer";
    String BODY = "body";
    String OWNER = "owner";
    String TEAM = "team";


    /**
     * 关闭弹窗
     * @param driver
     * @return
     */
    Boolean closeWindowClass(WebDriver driver);

    /**
     * 选择菜单
     * @param driver
     * @param subMenuValue
     */
    void chooseMenubarPage(WebDriver driver, String subMenuValue);

    /**
     * 进入选择弹窗
     * @param object
     * @return
     */
    WebElement selectComboBox(Object object);

    /**
     * 点击基础元素（无点击期望）
     * @param obj
     * @param element
     * @return
     */
    boolean clickValue(Object obj, UIBase element);

    /**
     * 给基础元素设值
     * @param obj
     * @param element
     * @param value
     * @return
     */
    boolean setValue(Object obj, UIBase element, Object value);

    /**
     * @param webElement
     * @param value
     * @return
     */
    boolean setValue(WebElement webElement, Object value);

    List<WebElement> findEles(Object obj, UIBase element);

    /**
     * 获取元素个数
     * @param obj
     * @param element
     * @return
     */
    int getSize(Object obj, UIBase element);
    /**
     * 查找元素
     * @param obj
     * @param element
     * @return
     */
    WebElement findEle(Object obj, UIBase element);

    /**
     * 查找元素
     * @param obj
     * @param element
     * @param index
     * @return
     */
    WebElement findEle(Object obj, UIBase element, int index);
}
