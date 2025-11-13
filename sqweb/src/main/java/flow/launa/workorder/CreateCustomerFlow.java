package flow.launa.workorder;

import entity.customerandcar.CustomerInfo;
import groovy.lang.MetaClassImpl;
import org.openqa.selenium.WebDriver;

public interface CreateCustomerFlow {

    /**
     * 简化设值
     * @param valueString
     * @return
     */
    CustomerInfo setValue(String valueString);

    /**
     * 新增客户页面 性别选择
     */
    void chooseGender(WebDriver driver, String gender);

    /**
     * 新增客户页面 客户类型选择
     */
    void selectCustomerType(WebDriver driver, String customerType);
    /**
     * 新增客户页面 车主来源选择
     */
    void selectOwnerSource(WebDriver driver, String ownerSource);
    /**
     *新增客户页面 车主类型选择
     */
    void selectOwnerType(WebDriver driver, String ownerType);

    /**
     * 新增客户页面 生日日期选择
     */
    void selectBirthdayDate(WebDriver driver, String birthdayDate);

    /**
     *新增客户页面 地址省、事、区选择
     */
    void selectAddress(WebDriver driver, String address);

    /**
     * 创建新客户
     * @param driver
     * @param customerInfo
     */
    void addCustomer(WebDriver driver, CustomerInfo customerInfo);
}
