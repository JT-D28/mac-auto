package flow.launa.workorder.impl;

import com.alibaba.fastjson.JSON;
import elementpath.PageElePath;
import entity.customerandcar.CustomerInfo;
import enu.ui.launa.web.commonbusiness.AddCustomerPageUI;
import enu.ui.launa.web.commonbusiness.CustomerListPageUI;
import flow.launa.workorder.CreateCustomerFlow;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.testng.Assert;
import page.object.launa.web.commonbusiness.AddCustomerPage;
import page.object.launa.web.commonbusiness.CustomerListPage;

import java.util.List;

@Component(value = "createCustomerFlow")
public class CreateCustomerFlowImpl implements CreateCustomerFlow {
    @Autowired
    CustomerListPage customerListPage;
    @Autowired
    AddCustomerPage addCustomerPage;
    @Autowired
    PageElePath pageElePath;

    @Value("${launa.server.url}")
    String launaBase;
    @Override
    public CustomerInfo setValue(String valueString){
        return JSON.parseObject(valueString,CustomerInfo.class);
    }

    @Override
    public void chooseGender(WebDriver driver, String gender) {

    }

    @Override
    public void selectCustomerType(WebDriver driver, String customerType) {

    }

    @Override
    public void selectOwnerSource(WebDriver driver, String ownerSource) {

    }

    @Override
    public void selectOwnerType(WebDriver driver, String ownerType) {

    }

    @Override
    public void selectBirthdayDate(WebDriver driver, String birthdayDate) {

    }

    @Override
    public void selectAddress(WebDriver driver, String address) {

    }

    @Override
    public void addCustomer(WebDriver driver, CustomerInfo customerInfo){
        driver.get(launaBase+"/web/commonBusiness/customerList");

        //点击新增客户按钮，打开新增客户页面
        WebElement clickNewCustomerButtonEle = customerListPage.findEle(driver, CustomerListPageUI.createCustomerButton);
        Assert.assertTrue(pageElePath.click(clickNewCustomerButtonEle));

        //切换弹窗
//        Assert.assertTrue(pageElePath.changeWindow(driver,1));
        Assert.assertTrue(pageElePath.changeNextWindow(driver));

        if(customerInfo.getCustomerName() != null){
            addCustomerPage.setValue(driver,AddCustomerPageUI.customerName,customerInfo.getCustomerName());
        }
        if(customerInfo.getMobilePhone() != null){
            addCustomerPage.setValue(driver,AddCustomerPageUI.mobilePhone,customerInfo.getMobilePhone());
        }
        if(customerInfo.getOtherPhone() != null){
            addCustomerPage.setValue(driver,AddCustomerPageUI.otherPhone,customerInfo.getOtherPhone());
        }
        if(customerInfo.getGenderSex() !=null){
            addCustomerPage.clickGender(driver);
            addCustomerPage.selectSex(driver,customerInfo.getGenderSex());
        }
        if(customerInfo.getCustomerType() !=null){
            addCustomerPage.ClickCustomer(driver);
            addCustomerPage.SelectCustomerType(driver,customerInfo.getCustomerType());
        }
        if (customerInfo.getCarOwner() !=null){
            addCustomerPage.ClickCarOwner(driver);
            addCustomerPage.SelectCarOwner(driver,customerInfo.getCarOwner());
        }
        if (customerInfo.getCarOwnerType() !=null){
            addCustomerPage.CarOwnerType(driver);
            addCustomerPage.SelectCarOwnerType(driver,customerInfo.getCarOwnerType());
        }
        if (customerInfo.getBirthdayDate() !=null){
            addCustomerPage.setValue(driver,AddCustomerPageUI.BirthdayDate,customerInfo.getBirthdayDate());
        }
        if (customerInfo.getAddress() != null){
            WebElement clickAddress = addCustomerPage.findEle(driver,AddCustomerPageUI.address);
            pageElePath.click(clickAddress);
            addCustomerPage.setValue(driver,AddCustomerPageUI.address,customerInfo.getAddress());
        }
        if (customerInfo.getAddress1() != null){
            WebElement clickAddress1 = addCustomerPage.findEle(driver,AddCustomerPageUI.addressInput);
            pageElePath.click(clickAddress1);
            addCustomerPage.setValue(driver,AddCustomerPageUI.addressInput,customerInfo.getAddress1());
        }
        if (customerInfo.getDerDesc() != null){
            addCustomerPage.setValue(driver,AddCustomerPageUI.discountInput,customerInfo.getDerDesc());
        }
        WebElement saveButton = addCustomerPage.findEle(driver,AddCustomerPageUI.saveCustomerButton);
        pageElePath.click(saveButton);
    }
}






