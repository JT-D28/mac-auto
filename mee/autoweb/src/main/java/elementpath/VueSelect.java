package elementpath;

import lombok.SneakyThrows;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * @author yuxiangfeng
 */
public class VueSelect {

    private final SqWebElement element;
    private final boolean isMulti;
    private int maxIndex;
    private final int maxDeep=10;
    private List<WebElement> selectList;
    private List<WebElement> tabList;


    public VueSelect(WebElement element) {
        String className = element.getAttribute("class");

        String vueSelectName = "el-select-dropdown el-popper";
        if (className == null || !className.contains(vueSelectName)){
            throw new RuntimeException();
        }

        this.element = new SqWebElement(element);
        findSelectList(0);
        if (selectList == null){
            this.maxIndex = -1;
        }else {
            this.maxIndex = selectList.size();
        }

        isMulti = className.contains("is-multiple");

    }

    @SneakyThrows
    private void findSelectList(int deep){
        if (deep>maxDeep){
            this.selectList = new ArrayList<>();
            this.maxIndex = 0;
            System.out.println("找不到选择");
        }
        List<WebElement> selectList = this.element.findVisElements(By.tagName("li"));
        if (selectList == null || selectList.size()==0){
            deep++;
            Thread.sleep(500*deep);
            System.out.println("sleep"+deep);
            findSelectList(deep);
            return;
        }
        this.selectList = selectList;
        this.maxIndex = this.selectList.size();
    }

    public void changeTab(int index){
        if(index<0){
            return;
        }
        String className = "el-tabs__nav";
        if (tabList == null ){
            if (element.waitEleVis(By.className(className))){
                System.out.println("tabList初始化");
                tabList = element.findElementByCssSelectors(".el-tabs__item.is-top");
            }else {
                throw new RuntimeException("查找tab失败");
            }

        }
        if (tabList.size()<index){
            throw new RuntimeException("数组越界");
        }
        SqWebElement tabSqEle = new SqWebElement(tabList.get(index));
        if (tabSqEle.click()){
            findSelectList(0);
        }
    }

    private void setMaxIndex(){
        if (selectList == null){
            this.maxIndex = -1;
        }else {
            this.maxIndex = selectList.size();
        }
    }

    public WebElement getWrappedElement() {
        return element.getWebElement();
    }
    public List<WebElement> getSelectList() {
        return selectList;
    }
    public List<WebElement> getAllSelected() {
        return getSelectList().stream().filter(VueSelect::isSelected).collect(Collectors.toList());
    }

    public boolean isMultiple() {
        return isMulti;
    }

    public void selectAll(){
        if (!isMulti || selectList == null){
            return;
        }
        for (WebElement ele: selectList){
            setSelected(ele,true);
        }
    }

    public void deselectAll(){
        if (!isMulti || selectList == null){
            return;
        }
        for (WebElement ele: selectList){
            setSelected(ele,false);
        }
    }

    public Boolean selectByIndex(int index,String hopeUrl) {
        selectByIndex(index);
        return element.hopeUrl(hopeUrl);
    }

        public void selectByIndex(int index) {
        if (index > maxIndex){
            throw new RuntimeException("selectByIndex error : index=" + index + ",maxIndex=" +maxIndex);
        }
        setSelected(selectList.get(index),true);
    }

    public void selectByIndexes(List<Integer> indexes) {
        if (!isMulti || indexes == null){
            throw new RuntimeException("selectByIndexes error :" +isMulti + indexes.toString());
        }
        for (int index:indexes){
            selectByIndex(index);
        }
    }

    public void selectByValue(String value) {
        if (value == null){
            return;
        }
        WebElement webElement = findEle(By.xpath(".//span[text()=\""+value+"\"]"));
        setSelected(webElement,true);
    }

    private WebElement findEle(By by){
        return element.findElement(by);
    }


    public void selectByContainsValue(String value) {
        if (value == null){
            return;
        }
        List<WebElement> webElementList = findEles(By.xpath(".//span[contains(text(),\""+value+"\")]"));
        if (webElementList == null){
            return;
        }
        for (WebElement webElement:webElementList){
            setSelected(webElement,true);
        }

    }

    private List<WebElement> findEles(By by){
        return element.findElements(by);
    }

    public void selectByValues(List<String> values) {
        if (!isMulti || values == null){
            return;
        }
        for (String value:values){
            selectByValue(value);
        }
    }

    private void setSelected(WebElement ele,boolean select){
        if (select == !isSelected(ele)){
            click(ele);
        }
    }

    private static Boolean isSelected(WebElement isSelect){
        String className = isSelect.getAttribute("class");

        String vueSelectName = "selected";
        if (className == null ){
            throw new RuntimeException("className is null");
        }
        if (className.contains(vueSelectName)){
            return true;
        }
        return false;
    }

    private void click(WebElement webElement){
        SqWebElement sqWebElement = new SqWebElement(webElement);
        sqWebElement.click();
    }
}
