package page.object.launa.web.workorder.impl;

import elementpath.PageElePath;
import elementpath.VueSelect;
import enu.ui.launa.web.workorder.EditWorkOrderPageUI;
import lombok.extern.slf4j.Slf4j;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import page.object.launa.web.impl.BasePageImpl;
import page.object.launa.web.workorder.EditWorkOrderPage;
import ui.annotaion.UIActLog;

import java.util.List;

/**
 * @author fengyuxiang
 */
@Slf4j
@Component
public class EditWorkOrderPageImpl extends BasePageImpl implements EditWorkOrderPage {

    @Autowired
    PageElePath pageElePath;

//    @UIActLog
//    private WebElement intoMemberItemChoose(Object object) {
//        String testId = "vipItemDialog";
//        return pageElePath.selectByTestId(object,testId);
//    }
//    private WebElement intoConstructor(Object object) {
//        String testId = "achConstructor";
//        return pageElePath.selectByTestId(object,testId);
//    }
//    private WebElement intoSales(Object object) {
//        String testId = "achSales";
//        return pageElePath.selectByTestId(object,testId);
//    }
//    private Object isPopup(Object object, Boolean isPopup){
//        if (isPopup != null && isPopup){
//            return intoPartsChooseOfItem(object);
//        }
//        return object;
//    }
//    private WebElement intoPartsChooseOfItem(Object object) {
//        String testId = "配件弹框";
//        return pageElePath.selectByTestId(object,testId);
//    }

    @UIActLog
    private Boolean chooseSales(WebElement containerEle, List<Integer> saleIndexList) {
//        //点击选择销售人员
//        WebElement salesEle = findEle(containerEle,EditWorkOrderPageUI.chooseSales);
//        if (!pageElePath.clickHopeBox(salesEle)) {
//            return false;
//        }
//
//        //进入销售人员区域
//        WebElement comboBoxEle = selectComboBox(((RemoteWebElement) containerEle).getWrappedDriver());
//        VueSelect select = new VueSelect(comboBoxEle);
//        select.selectByIndexes(saleIndexList);
//        return true;
        return false;
    }

    @Override
    @UIActLog
    public Boolean startTimeInput(WebDriver driver, String startTime) {
//        // TODO:弹框中直接选择时间，而不是通过传入String类型的时间
//        if (!setValue(driver, EditWorkOrderPageUI.startTimeInputEle,startTime)) {
//            return false;
//        }
//        //点击确认按钮
//        return clickValue(driver,EditWorkOrderPageUI.confirmButtonOfTimeBoxEle);
        return false;
    }

    /**
     * 点击新增项目按钮
     * @param driver
     * @param itemIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean clickCreateItem(WebDriver driver,int itemIndex) {
        int itemSizeBefore = 0;
        if(itemIndex != 0 ){
            itemSizeBefore = getSize(driver,EditWorkOrderPageUI.itemTr);
        }
        WebElement createItemButtonEle = findEle(driver,EditWorkOrderPageUI.clickCreateItemButton);
        if (!pageElePath.click(createItemButtonEle)){
            return false;
        }
        int itemSizeAfter = getSize(driver,EditWorkOrderPageUI.itemTr);
        if (itemSizeAfter - itemSizeBefore == 1){
            return true;
        }
        return false;
    }

    /**
     * 点击项目名称输入框
     * @param driver
     * @param index
     * @return
     */
    @Override
    @UIActLog
    public Boolean clickInputItem(WebDriver driver, int index) {
        WebElement itemTrEle = findEle(driver,EditWorkOrderPageUI.itemTr,index);
        WebElement itemNameEle = findEle(itemTrEle,EditWorkOrderPageUI.itemNames);
        return pageElePath.clickHopeBox(itemNameEle);
    }

    /**
     * 点击项目名称输入框
     * @param driver
     * @param index
     * @return
     */
    @Override
    @UIActLog
    public Boolean inputItemSendKey(WebDriver driver, int index, String itemName) {
        WebElement itemTrEle = findEle(driver,EditWorkOrderPageUI.itemTr,index);
        WebElement itemNameEle = findEle(itemTrEle,EditWorkOrderPageUI.itemNames);
        return setValue(itemNameEle,itemName);
    }

    /**
     * 选择项目
     * @param driver
     * @param tabIndex
     * @param itemIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean chooseItem(WebDriver driver, int tabIndex, int itemIndex) {
        //进入项目选择弹窗
        WebElement comboBoxEle = selectComboBox(driver);

        VueSelect select = new VueSelect(comboBoxEle);
        select.changeTab(tabIndex);
        select.selectByIndex(itemIndex);

        return true;
    }


    @Override
    @UIActLog
    public Boolean chooseConstructorInItem(WebDriver driver, int itemIndex, List<Integer> constructorIndexList) {
//        //点击选择施工人员
//        WebElement servInfoContainerEle = intoServInfoContainer(driver, itemIndex);
//        String testId = "选择施工人员";
//        WebElement chooseConstructorInItemEle = pageElePath.selectByTestId(servInfoContainerEle, testId);
//        if (!pageElePath.clickHopeBox(chooseConstructorInItemEle)) {
//            return false;
//        }
//        //进入施工人员区域
//        WebElement comboBoxEle = selectComboBox(driver);
//        VueSelect select = new VueSelect(comboBoxEle);
//        select.selectByIndexes(constructorIndexList);
        return false;
    }


    @Override
    @UIActLog
    public Boolean chooseSalesInItem(WebDriver driver, int itemIndex, List<Integer> constructorIndexList) {
//        //点击选择销售人员
//        WebElement servInfoContainer = intoServInfoContainer(driver, itemIndex);
//        return chooseSales(servInfoContainer, constructorIndexList);
        return false;
    }

    @Override
    @UIActLog
    public Boolean fixConstructorAch(WebDriver driver, int itemIndex, int constructorIndex, String achAmount) {
//        WebElement servInfoContainerEle = intoServInfoContainer(driver, itemIndex);
//        WebElement constructorAchEle = intoConstructor(servInfoContainerEle);
//        String className = "el-input__inner";
//        WebElement achInputEle = pageElePath.selectByClassNames(constructorAchEle, className, constructorIndex);
//        return pageElePath.sendKey(achInputEle, achAmount);
        return false;
    }


    @Override
    @UIActLog
    public Boolean fixSalesAch(WebDriver driver, int itemIndex, int salesIndex, String achAmount) {
//        WebElement servInfoContainerEle = intoServInfoContainer(driver, itemIndex);
//        WebElement salesEle = intoSales(servInfoContainerEle);
//        String className = "el-input__inner";
//        WebElement salesAchInputEle = pageElePath.selectByClassNames(salesEle, className, salesIndex);
//        return pageElePath.sendKey(salesAchInputEle, achAmount);
        return false;
    }

    /**
     * 修改工时
     * @param driver
     * @param itemIndex
     * @param itemManHour
     * @return
     */
    @Override
    @UIActLog
    public Boolean itemManHourInput(WebDriver driver, int itemIndex, String itemManHour) {
        WebElement itemTrEle = findEle(driver,EditWorkOrderPageUI.itemTr, itemIndex);
        WebElement itemHourEle = findEle(itemTrEle,EditWorkOrderPageUI.itemHour);
        return setValue(itemHourEle,itemManHour);
    }

    /**
     * 修改售价
     * @param driver
     * @param itemIndex
     * @param itemPrice
     * @return
     */
    @Override
    @UIActLog
    public Boolean itemPriceInput(WebDriver driver, int itemIndex, String itemPrice) {
        WebElement itemTrEle = findEle(driver,EditWorkOrderPageUI.itemTr, itemIndex);
        WebElement itemPriceEle = findEle(itemTrEle,EditWorkOrderPageUI.itemPrice);
        return setValue(itemPriceEle,itemPrice);
    }

    /**
     * 修改折扣
     * @param driver
     * @param itemIndex
     * @param itemDiscount
     * @return
     */
    @Override
    @UIActLog
    public Boolean itemDiscountInput(WebDriver driver, int itemIndex, String itemDiscount) {
        WebElement itemTrEle = findEle(driver,EditWorkOrderPageUI.itemTr, itemIndex);
        WebElement itemDiscountEle = findEle(itemTrEle,EditWorkOrderPageUI.itemDiscount);
        return setValue(itemDiscountEle,itemDiscount);
    }

    /**
     * 添加备注
     * @param driver
     * @param itemIndex
     * @param desc
     * @return
     */
    @Override
    @UIActLog
    public Boolean descInputInput(WebDriver driver, int itemIndex, String desc) {
        WebElement itemTrEle = findEle(driver,EditWorkOrderPageUI.itemTr, itemIndex);
        WebElement itemDescButtonEle = findEle(itemTrEle,EditWorkOrderPageUI.itemDescButton);
        WebElement itemDescEle =click(itemDescButtonEle,EditWorkOrderPageUI.itemDesc, itemIndex);
        if (itemDescEle == null){
            return false;
        }
        return setValue(itemDescEle,desc);
    }

    /**
     * 点击确认项目
     * @param driver
     * @param itemIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean confirmItem(WebDriver driver, int itemIndex) {
        WebElement itemTrEle = findEle(driver,EditWorkOrderPageUI.itemTr, itemIndex);
        WebElement confirmItemButtonEle = findEle(itemTrEle,EditWorkOrderPageUI.confirmItem);
        return click(confirmItemButtonEle,itemTrEle,EditWorkOrderPageUI.editItem)!= null;
    }

    /**
     * 编辑项目
     * @param driver
     * @param itemIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean editItem(WebDriver driver, int itemIndex) {
        WebElement itemTrEle = findEle(driver,EditWorkOrderPageUI.itemTr,itemIndex);
        WebElement editItemButtonEle = findEle(itemTrEle,EditWorkOrderPageUI.editItem);
        return click(editItemButtonEle,itemTrEle,EditWorkOrderPageUI.confirmItem)!= null;
    }

    /**
     * 删除项目
     * @param driver
     * @param itemIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean deleteItem(WebDriver driver, int itemIndex) {
        int itemSizeBefore = getSize(driver,EditWorkOrderPageUI.itemTr);
        WebElement deleteItemButtonEle = findEle(driver,EditWorkOrderPageUI.deleteItem,itemIndex);
        if (!pageElePath.click(deleteItemButtonEle)){
            return false;
        }
        int itemSizeAfter = getSize(driver,EditWorkOrderPageUI.itemTr);
        if (itemSizeBefore - itemSizeAfter == 1){
            return true;
        }
        return false;
    }

    /**
     * 编辑配件/退出编辑配件
     * @param driver
     * @param itemIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean editPartsInItem(WebDriver driver, int itemIndex) {
        WebElement itemTrEle = findEle(driver, EditWorkOrderPageUI.itemTr, itemIndex);
        WebElement editPartsByItemButtonEle = findEle(itemTrEle, EditWorkOrderPageUI.editPartOfItem);
        return pageElePath.click(editPartsByItemButtonEle);
    }

    /**
     * 点击新增会员项目
     * @param driver
     * @return
     */
    @Override
    @UIActLog
    public Boolean clickCreateMemberItem(WebDriver driver) {
        WebElement clickCreateMemberItemButtonEle = findEle(driver,EditWorkOrderPageUI.addVipItemButton);
        //TODO vipItemDialog 没有了，需重写
        return pageElePath.click(clickCreateMemberItemButtonEle, pageElePath.byTestIdSelect("vipItemDialog"));
    }


    @Override
    @UIActLog
    public Boolean chooseMemberItem(WebDriver driver, int index) {
//        WebElement memberItemChooseEle = intoMemberItemChoose(driver);
//        String className = "el-checkbox__inner";
//        WebElement memberItemEle = pageElePath.selectByClassNames(memberItemChooseEle, className, index);
//        //TODO 点击成功依据：该元素多了 is-checked 的class
//        return pageElePath.click(memberItemEle);
        return false;
    }


    @Override
    @UIActLog
    public Boolean closeMemberItemFrame(WebDriver driver) {
//        WebElement memberItemChooseEle = intoMemberItemChoose(driver);
//        WebElement closeButtonEle = pageElePath.selectByTagNames(memberItemChooseEle, "button", 0);
//        //TODO 点击成功依据：弹窗消失
//        return pageElePath.click(closeButtonEle);
        return false;
    }


    @Override
    @UIActLog
    public Boolean confirmMemberItem(WebDriver driver) {
//        WebElement memberItemChooseEle = intoMemberItemChoose(driver);
//        WebElement confirmButtonEle = pageElePath.selectByTagNames(memberItemChooseEle, "button", 1);
//        //TODO 点击成功依据：弹窗消失,并且增加一个会员服务项目
//        return pageElePath.click(confirmButtonEle);
        return false;
    }

    /**
     * 点击项目中的新增配件
     * @param driver
     * @param itemIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean clickCreatePartsInItem(WebDriver driver, int itemIndex) {
        WebElement partsInfoInItemEle = findEle(driver, EditWorkOrderPageUI.partsInfoInItem, itemIndex);
        WebElement addNewPartsInItemButtonEle = findEle(partsInfoInItemEle, EditWorkOrderPageUI.addNewPartsInItem);
        return pageElePath.click(addNewPartsInItemButtonEle);
    }

    /**
     * 工单中点击新增配件
     * @param driver
     * @return
     */
    @Override
    @UIActLog
    public Boolean clickCreateParts(WebDriver driver) {
        WebElement addNewPartsButtonEle = findEle(driver, EditWorkOrderPageUI.addNewParts);
        return pageElePath.click(addNewPartsButtonEle);
    }

    /**
     * 点击保存配件（项目中）
     * @param driver
     * @param itemIndex
     * @param partIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean savePartsInItem(WebDriver driver,int itemIndex,int partIndex){
        WebElement partsInfoInItemEle = findEle(driver, EditWorkOrderPageUI.partsInfoInItem, itemIndex);
        WebElement partsTrEle = findEle(partsInfoInItemEle,EditWorkOrderPageUI.partTrInItem,partIndex);
        WebElement savePartsInItemButtonEle = findEle(partsTrEle, EditWorkOrderPageUI.confirmPart);
        //由于savePartsInItemButtonEle在td下，savePartsInItemButtonEle.isDisplayed()为false，所以只能强制点击
        return pageElePath.clickForce(savePartsInItemButtonEle);
    }

    /**
     * 点击保存配件（工单中）
     * @param driver
     * @param partIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean saveParts(WebDriver driver,int partIndex){
        WebElement partsTrEle = findEle(driver,EditWorkOrderPageUI.partTr,partIndex);
        WebElement savePartsButtconfironEle = findEle(partsTrEle, EditWorkOrderPageUI.confirmPart);
        return pageElePath.clickForce(savePartsButtconfironEle);
    }
    /**
     * 删除配件
     * @param driver
     * @param partIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean deletePart(WebDriver driver,int partIndex) {
        WebElement partsTrEle = findEle(driver,EditWorkOrderPageUI.partTr,partIndex);
        WebElement deletePartButtonEle = findEle(partsTrEle, EditWorkOrderPageUI.deletePart);
        return pageElePath.click(deletePartButtonEle);
    }
    /**
     * 删除配件（项目中）
     * @param driver
     * @param partIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean deletePartInItem(WebDriver driver,int itemIndex,int partIndex){
        WebElement partsInfoInItemEle = findEle(driver, EditWorkOrderPageUI.partsInfoInItem, itemIndex);
        WebElement partsTrEle = findEle(partsInfoInItemEle,EditWorkOrderPageUI.partTrInItem,partIndex);
        WebElement deletePartButtonInItemEle = findEle(partsTrEle, EditWorkOrderPageUI.deletePart);
        return pageElePath.click(deletePartButtonInItemEle);
    }
    /**
     * 编辑配件
     * @param driver
     * @param partIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean editPart(WebDriver driver,int partIndex) {
        WebElement partsTrEle = findEle(driver,EditWorkOrderPageUI.partTr,partIndex);
        WebElement editPartButtonEle = findEle(partsTrEle, EditWorkOrderPageUI.editPart);
        return pageElePath.click(editPartButtonEle);
    }
    /**
     * 编辑配件（项目中）
     * @param driver
     * @param partIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean editPartInItem(WebDriver driver,int itemIndex,int partIndex){
        WebElement partsInfoInItemEle = findEle(driver, EditWorkOrderPageUI.partsInfoInItem, itemIndex);
        WebElement partsTrEle = findEle(partsInfoInItemEle,EditWorkOrderPageUI.partTrInItem,partIndex);
        WebElement editPartButtonInItemEle = findEle(partsTrEle, EditWorkOrderPageUI.editPart);
        return pageElePath.click(editPartButtonInItemEle);
    }

    private Boolean clickInputPart(WebElement partTrEle) {
        WebElement partNameEle = findEle(partTrEle,EditWorkOrderPageUI.partName);
        return pageElePath.clickHopeBox(partNameEle);
    }

    /**
     * 点击配件名称
     * @param driver
     * @param partIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean clickInputPart(WebDriver driver,int partIndex){
        WebElement partsTrEle = findEle(driver,EditWorkOrderPageUI.partTr,partIndex);
        return clickInputPart(partsTrEle);
    }

    /**
     * 点击配件名称（项目中）
     * @param driver
     * @param partIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean clickInputPartInItem(WebDriver driver,int itemIndex,int partIndex){
        WebElement partsInfoInItemEle = findEle(driver, EditWorkOrderPageUI.partsInfoInItem, itemIndex);
        WebElement partsTrEle = findEle(partsInfoInItemEle,EditWorkOrderPageUI.partTrInItem,partIndex);
        return clickInputPart(partsTrEle);
    }

    private Boolean inputPartSendKey(WebElement partTrEle, String itemName) {
        WebElement partNameEle = findEle(partTrEle,EditWorkOrderPageUI.partName);
        return setValue(partNameEle,itemName);
    }

    /**
     * 输入配件名称
     * @param driver
     * @param partIndex
     * @param partName
     * @return
     */
    @Override
    @UIActLog
    public Boolean inputPartSendKey(WebDriver driver,int partIndex ,String partName) {
        WebElement partsTrEle = findEle(driver,EditWorkOrderPageUI.partTr,partIndex);
        return inputPartSendKey(partsTrEle,partName);
    }

    /**
     * 输入配件名称（项目中）
     * @param driver
     * @param partIndex
     * @param partName
     * @return
     */
    @Override
    @UIActLog
    public Boolean inputPartSendKeyInItem(WebDriver driver,int itemIndex,int partIndex ,String partName) {
        WebElement partsInfoInItemEle = findEle(driver, EditWorkOrderPageUI.partsInfoInItem, itemIndex);
        WebElement partsTrEle = findEle(partsInfoInItemEle,EditWorkOrderPageUI.partTrInItem,partIndex);
        return inputPartSendKey(partsTrEle,partName);
    }

    /**
     * 选择配件
     * @param driver
     * @param tabIndex
     * @param partIndex
     * @return
     */
    @Override
    @UIActLog
    public Boolean selectPart(WebDriver driver, int tabIndex, int partIndex) {
        WebElement comboBoxEle = selectComboBox(driver);
        VueSelect select = new VueSelect(comboBoxEle);
        select.changeTab(tabIndex);
        select.selectByIndex(partIndex);
        return true;
    }



    private Boolean partNumEdit(WebElement partTrEle, String partNum) {
        WebElement partNumEle = findEle(partTrEle,EditWorkOrderPageUI.partNum);
        return setValue(partNumEle,partNum);
    }



    /**
     * 配件数量编辑
     * @param driver
     * @param partIndex
     * @param partNum
     * @return
     */
    @Override
    @UIActLog
    public Boolean partNumEdit(WebDriver driver,int partIndex,String partNum){
        WebElement partsTrEle = findEle(driver,EditWorkOrderPageUI.partTr,partIndex);
        return partNumEdit(partsTrEle,partNum);
    }

    /**
     * 配件数量编辑（项目中）
     * @param driver
     * @param itemIndex
     * @param partIndex
     * @param partNum
     * @return
     */
    @Override
    @UIActLog
    public Boolean partNumEditInItem(WebDriver driver, int itemIndex, int partIndex, String partNum){
        WebElement partsInfoInItemEle = findEle(driver, EditWorkOrderPageUI.partsInfoInItem, itemIndex);
        WebElement partsTrEle = findEle(partsInfoInItemEle,EditWorkOrderPageUI.partTrInItem,partIndex);
        return partNumEdit(partsTrEle,partNum);
    }

    private Boolean partPriceEdit(WebElement partTrEle, String partPrice) {
        WebElement partPriceEle = findEle(partTrEle,EditWorkOrderPageUI.partPrice);
        return setValue(partPriceEle,partPrice);
    }

    /**
     * 配件价格编辑
     * @param driver
     * @param partIndex
     * @param partPrice
     * @return
     */
    @Override
    @UIActLog
    public Boolean partPriceEdit(WebDriver driver,int partIndex,String partPrice){
        WebElement partsTrEle = findEle(driver,EditWorkOrderPageUI.partTr,partIndex);
        return partPriceEdit(partsTrEle,partPrice);
    }

    /**
     * 配件价格编辑（项目中）
     * @param driver
     * @param itemIndex
     * @param partIndex
     * @param partPrice
     * @return
     */
    @Override
    @UIActLog
    public Boolean partPriceEditInItem(WebDriver driver, int itemIndex, int partIndex, String partPrice){
        WebElement partsInfoInItemEle = findEle(driver, EditWorkOrderPageUI.partsInfoInItem, itemIndex);
        WebElement partsTrEle = findEle(partsInfoInItemEle,EditWorkOrderPageUI.partTrInItem,partIndex);
        return partPriceEdit(partsTrEle,partPrice);
    }

    private Boolean partDiscountEdit(WebElement partTrEle, String partDiscount) {
        WebElement partDiscountEle = findEle(partTrEle,EditWorkOrderPageUI.partDiscount);
        return setValue(partDiscountEle,partDiscount);
    }

    /**
     * 配件折扣编辑
     * @param driver
     * @param partIndex
     * @param partPrice
     * @return
     */
    @Override
    @UIActLog
    public Boolean partDiscountEdit(WebDriver driver,int partIndex,String partPrice){
        WebElement partsTrEle = findEle(driver,EditWorkOrderPageUI.partTr,partIndex);
        return partDiscountEdit(partsTrEle,partPrice);
    }

    /**
     * 配件折扣编辑（项目中）
     * @param driver
     * @param itemIndex
     * @param partIndex
     * @param partPrice
     * @return
     */
    @Override
    @UIActLog
    public Boolean partDiscountEditInItem(WebDriver driver, int itemIndex, int partIndex, String partPrice){
        WebElement partsInfoInItemEle = findEle(driver, EditWorkOrderPageUI.partsInfoInItem, itemIndex);
        WebElement partsTrEle = findEle(partsInfoInItemEle,EditWorkOrderPageUI.partTrInItem,partIndex);
        return partDiscountEdit(partsTrEle,partPrice);
    }

    private Boolean partRemarkEdit(WebElement partTrEle, String partRemark){
        WebElement partRemarkButtonEle = findEle(partTrEle,EditWorkOrderPageUI.partDescButton);
        WebElement partRemarkEle = click(partRemarkButtonEle,EditWorkOrderPageUI.partDesc,0);
        if (partRemarkEle == null){
            return false;
        }
        return setValue(partRemarkEle,partRemark);
    }

    /**
     * 配件备注编辑
     * @param driver
     * @param partIndex
     * @param partPrice
     * @return
     */
    @Override
    @UIActLog
    public Boolean partRemarkEdit(WebDriver driver,int partIndex,String partPrice){
        WebElement partsTrEle = findEle(driver,EditWorkOrderPageUI.partTr,partIndex);
        return partRemarkEdit(partsTrEle,partPrice);
    }

    /**
     * 配件备注编辑（项目中）
     * @param driver
     * @param itemIndex
     * @param partIndex
     * @param partPrice
     * @return
     */
    @Override
    @UIActLog
    public Boolean partRemarkEditInItem(WebDriver driver, int itemIndex, int partIndex, String partPrice){
        WebElement partsInfoInItemEle = findEle(driver, EditWorkOrderPageUI.partsInfoInItem, itemIndex);
        WebElement partsTrEle = findEle(partsInfoInItemEle,EditWorkOrderPageUI.partTrInItem,partIndex);
        return partRemarkEdit(partsTrEle,partPrice);
    }


    @Override
    @UIActLog
    public Boolean clickCreateParts(Object object, Boolean isPopup) {
//        Object partsChooseOfItemEle = isPopup(object, isPopup);
//        String testId = "新增配件";
//        WebElement createPartsEle = pageElePath.selectByTestId(partsChooseOfItemEle, testId);
//        return pageElePath.click(createPartsEle, pageElePath.byTestIdSelect("editParts"));
        return false;
    }


    @Override
    @UIActLog
    public Boolean clickPartsName(Object object, Boolean isPopup) {
//        Object partsChooseObj = isPopup(object, isPopup);
//        WebElement editPartsContainerEle = intoEditPartsContainer(partsChooseObj);
//        String cssName = "[placeholder=\"配件名称/OE码/规格型号\"]";
//        WebElement partsNameEle = pageElePath.selectByCssSelector(editPartsContainerEle, cssName);
//        return pageElePath.clickHopeBox(partsNameEle);
        return false;
    }


    @Override
    @UIActLog
    public Boolean inputPartsSendKey(Object object, String partName, Boolean isPopup) {
//        Object partsChooseObj = isPopup(object, isPopup);
//        WebElement editPartsContainerEle = intoEditPartsContainer(partsChooseObj);
//        String cssName = "[placeholder=\"配件名称/OE码/规格型号\"]";
//        WebElement partsNameInputEle = pageElePath.selectByCssSelector(editPartsContainerEle, cssName);
//        return pageElePath.sendKey(partsNameInputEle, partName);
        return false;
    }


    @Override
    @UIActLog
    public Boolean chooseParts(Object object, Boolean isPopup, int tabIndex, int partsIndex) {
//        //进入配件选择弹窗
//        WebElement comboBoxEle = selectComboBox(object);
//
//        VueSelect select = new VueSelect(comboBoxEle);
//        select.changeTab(tabIndex);
//        select.selectByIndex(partsIndex);
//
//        return true;
        return false;
    }


    @Override
    @UIActLog
    public Boolean chooseSalesInPart(WebDriver driver, Boolean isPopup, List<Integer> saleIndexList) {
//        //点击选择销售人员
//        WebElement editPartsContainerEle = intoEditPartsContainer(
//                isPopup(driver, isPopup));
//        return chooseSales(editPartsContainerEle, saleIndexList);
        return false;
    }


    @Override
    @UIActLog
    public Boolean fixSalesAchInPart(WebDriver driver, Boolean isPopup, int salesIndex, String achAmount) {
//        Object partsChooseObj = isPopup(driver, isPopup);
//        WebElement salesAchEle = intoSales(partsChooseObj);
//        String className = "el-input__inner";
//        WebElement salesAchInputEle = pageElePath.selectByClassNames(salesAchEle, className, salesIndex);
//        return pageElePath.sendKey(salesAchInputEle, achAmount);
        return false;
    }


    @Override
    @UIActLog
    public Boolean partsNumberEdit(Object object, String number, Boolean isPopup) {
//        Object partsChooseObj = isPopup(object, isPopup);
//        WebElement editPartsContainerEle = intoEditPartsContainer(partsChooseObj);
//        String testId = "配件数量";
//        WebElement partNumberInputEle = pageElePath.selectByTestId(editPartsContainerEle, testId);
//        return pageElePath.sendKey(partNumberInputEle, number);
        return false;
    }


    @Override
    @UIActLog
    public Boolean partsPriceEdit(Object object, String price, Boolean isPopup) {
//        Object partsChooseObj = isPopup(object, isPopup);
//        WebElement editPartsContainerEle = intoEditPartsContainer(partsChooseObj);
//        String testId = "配件售价";
//        WebElement partsPriceInputEle = pageElePath.selectByTestId(editPartsContainerEle, testId);
//        return pageElePath.sendKey(partsPriceInputEle, price);
        return false;
    }


    @Override
    @UIActLog
    public Boolean partsDiscountEdit(Object object, String discount, Boolean isPopup) {
//        Object partsChooseObj = isPopup(object, isPopup);
//        WebElement editPartsContainer = intoEditPartsContainer(partsChooseObj);
//        String testId = "配件折扣";
//        WebElement partDiscountInputEle = pageElePath.selectByTestId(editPartsContainer, testId);
//        return pageElePath.sendKey(partDiscountInputEle, discount);
        return false;
    }

    @Override
    @UIActLog
    public Boolean partsDescEdit(Object object, String desc, Boolean isPopup) {
//        Object partsChooseObj = isPopup(object, isPopup);
//        WebElement editPartsContainer = intoEditPartsContainer(partsChooseObj);
//        String testId = "配件备注";
//        WebElement partDiscountInputEle = pageElePath.selectByTestId(editPartsContainer, testId);
//        return pageElePath.sendKey(partDiscountInputEle, desc);
        return false;
    }


    @Override
    @UIActLog
    public Boolean confirmParts(Object object, Boolean isPopup) {
//        Object partsChooseObj = isPopup(object, isPopup);
//        WebElement editPartsContainerEle = intoEditPartsContainer(partsChooseObj);
//        WebElement confirmPartEle = pageElePath.selectByTagNames(editPartsContainerEle, "button", 0);
//        //TODO 点击成功依据：
//        return pageElePath.click(confirmPartEle);
        return false;
    }


    @Override
    @UIActLog
    public Boolean cancelParts(Object object, Boolean isPopup) {
//        Object partsChooseObj = isPopup(object, isPopup);
//        WebElement editPartsContainerEle = intoEditPartsContainer(partsChooseObj);
//        WebElement cancelPartsButtonEle = pageElePath.selectByTagNames(editPartsContainerEle, "button", 1);
//        //TODO 点击成功依据：
//        return pageElePath.click(cancelPartsButtonEle);
        return false;
    }


    @Override
    @UIActLog
    public Boolean editParts(Object object, int partsIndex, Boolean isPopup) {
//        Object partsChooseObj = isPopup(object, isPopup);
//        WebElement partsInfoContainerEle = intoPartsInfoContainer(partsChooseObj, partsIndex);
//        WebElement editPartButtonEle = pageElePath.selectByTagNames(partsInfoContainerEle, "button", 0);
//        return pageElePath.click(editPartButtonEle, pageElePath.byTestIdSelect("editParts"));
        return false;
    }


    @Override
    @UIActLog
    public Boolean deleteParts(Object object, int partsIndex, Boolean isPopup) {
//        Object partsChooseObj = isPopup(object, isPopup);
//        WebElement partsInfoContainerEle = intoPartsInfoContainer(partsChooseObj, partsIndex);
//        WebElement deletePartbuttonEle = pageElePath.selectByTagNames(partsInfoContainerEle, "button", 1);
//        //TODO 点击成功依据：
//        return pageElePath.click(deletePartbuttonEle);
        return false;
    }


    @Override
    @UIActLog
    public Boolean savePartsInPopup(Object object) {
//        String testId = "保存";
//        WebElement savePartButtonEle = pageElePath.selectByTestId(object, testId);
//        //TODO 点击成功依据：
//        return pageElePath.click(savePartButtonEle);
        return false;
    }


    @Override
    @UIActLog
    public Boolean cancelPartsInPopup(Object object) {
//        String testId = "取消";
//        WebElement cancelPartsButtonEle = pageElePath.selectByTestId(object, testId);
//        //TODO 点击成功依据：
//        return pageElePath.click(cancelPartsButtonEle);
        return false;
    }


    @Override
    @UIActLog
    public Boolean salesPeopleChoose(WebDriver driver, int saleIndex) {
        //点击接车人
        WebElement salesPeopleEle =findEle(driver,EditWorkOrderPageUI.接车人INPUT);
        if (!pageElePath.clickHopeBox(salesPeopleEle)) {
            return false;
        }

        //进入接车人选择弹框
        WebElement comboBoxEle = selectComboBox(driver);
        VueSelect select = new VueSelect(comboBoxEle);
        select.selectByIndex(saleIndex);

        return true;
    }


    @Override
    @UIActLog
    public Boolean uploadPic(WebDriver driver, String filepath) {
        String className = "el-upload--picture-card";
        WebElement uploadPicEle = pageElePath.selectByClassName(driver, className);
        //TODO  点击成功依据：判断出现文件选择框
        return pageElePath.click(uploadPicEle)
                && pageElePath.uploadPic(filepath)
                && uploadPicIsSuccess(driver);
    }

    int picNum = 0;

    /**
     * 判断图片是否上传成功
     *
     * @param driver
     * @return
     */
    @UIActLog
    private Boolean uploadPicIsSuccess(WebDriver driver) {
        String cssName = ".el-upload-list__item";
        if (pageElePath.selectByCssSelectors(driver, cssName, picNum) == null) {
            log.error("上传失败");
            return false;
        }
        picNum++;
        return true;
    }

    /**
     * 鼠标悬停在图片上
     *
     * @param driver
     * @param picIndex
     * @return
     */
    @UIActLog
    private Boolean mouseOverInPic(WebDriver driver, int picIndex) {
        WebElement picLocationEle = findEle(driver,EditWorkOrderPageUI.picBox,picIndex);
        return pageElePath.actionChains(picLocationEle);
    }


    @Override
    @UIActLog
    public Boolean deletePic(WebDriver driver, int picIndex) {
        WebElement deletePicEle = findEle(driver,EditWorkOrderPageUI.deletePicButton,picIndex);
        //TODO 点击成功依据：
        return mouseOverInPic(driver, picIndex) && pageElePath.click(deletePicEle);
    }


    @Override
    @UIActLog
    public Boolean lookPic(WebDriver driver, int picIndex) {
        WebElement lookPicEle = findEle(driver,EditWorkOrderPageUI.lookPicButton,picIndex);
        //TODO 点击成功依据：
        return mouseOverInPic(driver, picIndex) && pageElePath.click(lookPicEle);
    }


    @Override
    @UIActLog
    public Boolean clickSaveButton(WebDriver driver) {
        WebElement saveOrderButtonEle = findEle(driver,EditWorkOrderPageUI.saveWorkOrderButton);
        //TODO  点击成功依据：页面url变化
        return pageElePath.click(saveOrderButtonEle);
    }

}
