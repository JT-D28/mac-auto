package page.object.autohome;

import entity.customerandcar.CarCategory;
import org.openqa.selenium.WebDriver;

/**
 * @author yuxiangfeng
 */
public interface Car {

    void getLevel1And2(WebDriver driver1);

    /**
     * 获取Level3车型
     * @param driver1
     * @param carCategory
     */
    void getLevel3(WebDriver driver1, CarCategory carCategory);

    void getLevel3V2(WebDriver driver1, CarCategory carCategory);
}
