package page.object.launa.web.commonbusiness.impl;

import elementpath.PageElePath;
import enu.ui.launa.web.commonbusiness.AddCustomerPageUI;
import enu.ui.launa.web.workorder.EditWorkOrderPageUI;
import lombok.extern.slf4j.Slf4j;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.testng.Assert;
import page.object.launa.web.commonbusiness.AddCustomerPage;
import page.object.launa.web.impl.BasePageImpl;

import java.util.ArrayList;


@Slf4j
@Component
public class AddCustomerPageImpl extends BasePageImpl implements AddCustomerPage {

    @Autowired
    PageElePath pageElePath;

    @Override
    public void clickInputName(WebDriver driver, String CarOwnerName) {
        WebElement customerNameEle = findEle(driver, AddCustomerPageUI.customerName);
        Assert.assertTrue(setValue(customerNameEle, CarOwnerName));
    }

    @Override
    public void clickInputMobilePhone(WebDriver driver, String MobilePhone) {
        WebElement MobilePhoneEle = findEle(driver, AddCustomerPageUI.mobilePhone);
        setValue(MobilePhoneEle, MobilePhone);
    }

    @Override
    public void clickOtherPhone(WebDriver driver, String OtherPhone) {
        WebElement OtherPhoneEle = findEle(driver, AddCustomerPageUI.otherPhone);
        setValue(OtherPhoneEle, OtherPhone);
    }

    @Override
    public void clickShortNumber(WebDriver driver, String ShortNumber) {
        WebElement ShortNumberEle = findEle(driver, AddCustomerPageUI.shortNumber);
        setValue(ShortNumberEle, ShortNumber);
    }

    @Override
    public void clickGender(WebDriver driver) {
        WebElement createGenderButtonEle = findEle(driver,AddCustomerPageUI.genderSex);
        Assert.assertTrue(pageElePath.click(createGenderButtonEle));
    }

    @Override
    public void selectSex(WebDriver driver, String Sex) {
//        WebElement genderSexList = findEle(driver,AddCustomerPageUI.genderSexList);
        if( Sex.equals("保密")){
            driver.findElement(By.xpath("/html/body/div[2]/div[1]/div[1]/ul/li[1]")).click();
        }
        if(Sex.equals("男")){
            driver.findElement(By.xpath("/html/body/div[2]/div[1]/div[1]/ul/li[2]")).click();
        }
        if(Sex.equals("女")){
            driver.findElement(By.xpath("/html/body/div[2]/div[1]/div[1]/ul/li[3]")).click();
        }
    }

    @Override
    public void ClickCustomer(WebDriver driver) {
        WebElement createCustomerButtonEle = findEle(driver,AddCustomerPageUI.customerType);
        Assert.assertTrue(pageElePath.click(createCustomerButtonEle));
    }

    @Override
    public void SelectCustomerType(WebDriver driver, String customerType) {

        if (customerType.equals("散客")){
            driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[1]/ul/li[1]")).click();
        }
        else if (customerType.equals("会员")){
            driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[1]/ul/li[2]")).click();
        }
    }

    @Override
    public void ClickCarOwner(WebDriver driver) {
        WebElement createCarOwnerEle = findEle(driver,AddCustomerPageUI.carOwner);
        Assert.assertTrue(pageElePath.click(createCarOwnerEle));
    }

    @Override
    public void SelectCarOwner(WebDriver driver, String selectCarOwner) {
        if (selectCarOwner.equals("附近社区") ){
            driver.findElement(By.xpath("/html/body/div[4]/div[1]/div[1]/ul/li[1]")).click();
        }
        else if (selectCarOwner.equals("朋友介绍") ){
            driver.findElement(By.xpath("/html/body/div[4]/div[1]/div[1]/ul/li[2]")).click();
        }
        else if (selectCarOwner.equals("线上关注") ){
            driver.findElement(By.xpath("/html/body/div[4]/div[1]/div[1]/ul/li[3]")).click();
        }
        else if (selectCarOwner.equals("其他")){
            driver.findElement(By.xpath("/html/body/div[4]/div[1]/div[1]/ul/li[4]")).click();
        }
    }

    @Override
    public void CarOwnerType(WebDriver driver) {
        WebElement createCarOwnerType = findEle(driver,AddCustomerPageUI.carOwnerType);
        Assert.assertTrue(pageElePath.click(createCarOwnerType));
    }

    @Override
    public void SelectCarOwnerType(WebDriver driver, String SelectCarOwnerType) {
        if (SelectCarOwnerType.equals("个人车主") ){
            driver.findElement(By.xpath("/html/body/div[2]/div[1]/div[1]/ul/ul[1]/li[2]/ul/li[1]")).click();
        }
        else if (SelectCarOwnerType.equals("出租车司机")){
            driver.findElement(By.xpath("/html/body/div[2]/div[1]/div[1]/ul/ul[1]/li[2]/ul/li[2]")).click();
        }
        else if (SelectCarOwnerType.equals("单位车司机")){
            driver.findElement(By.xpath("/html/body/div[2]/div[1]/div[1]/ul/ul[1]/li[2]/ul/li[3]")).click();
        }
        else if (SelectCarOwnerType.equals("卡车司机")){
            driver.findElement(By.xpath("/html/body/div[2]/div[1]/div[1]/ul/ul[1]/li[2]/ul/li[4]")).click();
        }
    }

    @Override
    public void SelectBirthdayDate(WebDriver driver, String SelectBirthdayDate) {
        WebElement BirthdayDateEle = findEle(driver, AddCustomerPageUI.BirthdayDate);
        Assert.assertTrue(setValue(BirthdayDateEle, SelectBirthdayDate));
    }

    @Override
    public void SelectAddress(WebDriver driver, String SelectAddress) {
        WebElement addressEle = findEle(driver, AddCustomerPageUI.address);
        Assert.assertTrue(pageElePath.click(addressEle));
        String[] SelectAddresslist = SelectAddress.split("\\/");
        System.out.println(SelectAddresslist);
        for (int i = 0; i < SelectAddresslist.length; ++i){
            System.out.println(SelectAddresslist[i]);
            java.util.List<WebElement> ul = driver.findElements(By.className("list-view"));
            String liList = ul.get(0).getText();
            System.out.println(liList);
//            list<String> xx = new ArrayList<>(Arraylist(ellipsoidDropDownListstr.split("\n")));
        }
        Assert.assertTrue(setValue(addressEle, SelectAddress));
    }

    @Override
    public void AddressInput(WebDriver driver, String AddressInput) {
        WebElement addressInputEle = findEle(driver, AddCustomerPageUI.addressInput);
        setValue(addressInputEle, AddressInput);
    }

    @Override
    public void DiscountInput(WebDriver driver, String derDesc) {
        WebElement derDescEle = findEle(driver, AddCustomerPageUI.discountInput);
        setValue(derDescEle, derDesc);
    }

    @Override
    public Boolean uploadPic(WebDriver driver, String filepath) {
        String className = "el-icon-plus";
        WebElement uploadPicEle = pageElePath.selectByClassName(driver, className);
        pageElePath.click(uploadPicEle);
        pageElePath.uploadPic(filepath);
        return true;
    }

    @Override
    public Boolean deletePic(WebDriver driver, int picIndex) {
        WebElement deletePicEle = findEle(driver, EditWorkOrderPageUI.deletePicButton,picIndex);
        return pageElePath.click(deletePicEle);
    }

    @Override
    public void ClickSaveCustomer(WebDriver driver) {
        WebElement saveCustomerButtonEle = findEle(driver,AddCustomerPageUI.saveCustomerButton);
        //TODO  点击成功依据：页面url变化
        pageElePath.click(saveCustomerButtonEle);
    }
}
