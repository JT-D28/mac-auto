package page.object.autohome.impl;

import dao.autohome.AutoHomeDao;
import elementpath.PageElePath;
import entity.customerandcar.CarCategory;
import lombok.extern.slf4j.Slf4j;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;
import page.object.autohome.Car;

import java.net.URL;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * @author yuxiangfeng
 */
@Slf4j
@Component
public class CarImpl implements Car {

    @Autowired
    AutoHomeDao autoHomeDao;

    @Autowired
    PageElePath pageElePath;

    WebDriver driver;
    List<CarCategory> tempList;
    List<CarCategory> carCategoryList1;
    List<CarCategory> carCategoryList2;
    Long waitTime = 5L;

    final List<String> idList;
    final String version = "1.1";

    int level;
    Long parentId;
    String firstLetter;
    String brand;
    String series;
    String year;
    String name;
    String precursor;
    String gear;
    int specId;

    WebElement firstNameEle = null;
    WebElement firstNameAfterClickEle = null;
    String firstNameEleStr = null;
    String firstNameAfterClickEleStr = null;

    public CarImpl(){
        tempList = new ArrayList<>();
        carCategoryList1 = new ArrayList<>();
        carCategoryList2 = new ArrayList<>();
        idList = Arrays.asList("A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","V","W","X","Y","Z");
    }


    @Override
    public void getLevel1And2(WebDriver driver1){
        this.driver = driver1;
        driver.get("https://www.autohome.com.cn/car/");

        for (String boxId :idList){
            WebElement boxEle = pageElePath.selectById(driver,"box"+boxId);
            WebElement buttonEle = driver.findElement(By.id("tab-content")).findElement(By.cssSelector("[data-meto=\""+boxId+"\"]"));
            Boolean s = pageElePath.click(buttonEle,boxEle,By.tagName("dl"));

            for (WebElement brandEle : pageElePath.selectListByTagName(boxEle,"dl")){
                WebElement brandItem = pageElePath.selectByCssSelector(brandEle,"dt > div > a");
                brand = brandItem.getText();
                String logo = brandItem.getAttribute("href");

                CarCategory carCategory1 = new CarCategory();
                carCategory1.setVersion(version);
                carCategory1.setLevel(1);
                carCategory1.setParentId(0L);
                carCategory1.setFirstLetter(boxId);
                carCategory1.setBrand(brand);
                carCategory1.setName(brand);
                carCategory1.setLogo(logo);
                carCategory1.setCarType("C");
                autoHomeDao.insert(carCategory1);

                for (WebElement seriesEle:pageElePath.selectByCssSelectors(brandEle,"li > h4 > a")){
                    String seriesName = seriesEle.getText();
                    if (seriesName.equals("特卖")){
                        continue;
                    }
                    String url = seriesEle.getAttribute("href");
                    CarCategory carCategory2 = new CarCategory();
                    carCategory2.setLevel(2);
                    carCategory2.setParentId(carCategory1.getId());
                    carCategory2.setFirstLetter(boxId);
                    carCategory2.setBrand(brand);
                    carCategory2.setSeries(seriesName);
                    carCategory2.setName(seriesName);
                    carCategory2.setCarType("C");
                    carCategory2.setUrl(url);
                    carCategoryList2.add(carCategory2);
                }

            }
        }

        tempList.clear();
        for (CarCategory carCategory:carCategoryList2){
            tempList.add(carCategory);
            if (tempList.size() == 500) {
                autoHomeDao.batchInsert(tempList);
                tempList.clear();
            }
        }
        autoHomeDao.batchInsert(tempList);
    }


    private void getCarCategory(String id){
        if (pageElePath.waitEle(driver,By.id(id),waitTime)) {
            //爬即将销售车型
            WebElement specWrap = pageElePath.selectById(driver,id);
            List<WebElement> dlEleList = pageElePath.selectListByTagName(specWrap,"dl");
            for (WebElement dlEle:dlEleList){
                WebElement dtEle = pageElePath.selectByTagName(dlEle,"dt");
                WebElement engineEle = pageElePath.selectByClassName(dtEle,"spec-name");
                String engine = engineEle.getText();
                for (WebElement ddEle:pageElePath.selectListByTagName(dlEle,"dd")){
                    if (id.equals("specWrap-2")){
                        year = ddEle.getAttribute("data-sift1");
                    }else if (id.equals("specWrap-1")){
                        year = "-1";
                    }
                    try {
                        WebElement nameEle = pageElePath.selectByClassName(ddEle,"name");
                        getNameAndSpecId(nameEle);
                    }catch (Exception e){
                        log.error("nameEle find error"+e.toString());
                        log.error("set name = 名字未找到 , specId = -");
                        name = "名字未找到";
                        specId = -1;
                    }
                    try {
                        precursor = pageElePath.selectByClassNames(ddEle,"type-default",0).getText();
                    }catch (Exception e){
                        log.error(""+e.toString());
                        log.error("set precursor=未知");
                        precursor="未知";
                    }

                    try {
                        gear = pageElePath.selectByClassNames(ddEle,"type-default",1).getText();
                    }catch (Exception e){
                        log.error(""+e.toString());
                        log.error("set gear=未知");
                        gear="未知";
                    }

                    CarCategory carCategory3 = new CarCategory();
                    carCategory3.setVersion(version);
                    carCategory3.setLevel(level);
                    carCategory3.setParentId(parentId);
                    carCategory3.setFirstLetter(firstLetter);
                    carCategory3.setBrand(brand);
                    carCategory3.setSeries(series);
                    carCategory3.setYear(year);
                    carCategory3.setName(name);
                    carCategory3.setCarType("C");
                    carCategory3.setEngine(engine);
                    carCategory3.setPrecursor(precursor);
                    carCategory3.setGear(gear);
                    carCategory3.setSpecId(specId);
                    tempList.add(carCategory3);
                    log.info(carCategory3.toString());
                }
            }
        }else {
            log.info(id + "is empty");
        }
    }

    private void updateData(){
        if (!tempList.isEmpty()){
            autoHomeDao.batchInsert(tempList);
        }else {
            log.info("tempList isEmpty");
        }
        autoHomeDao.modifyStatus(parentId,2);
        tempList.clear();
    }

    int maxDeep =100;
    private Boolean switchTab(WebElement li,int deep){
        if(deep>maxDeep){
            return false;
        }
        WebElement specWrap = pageElePath.selectById(driver,"specWrap-3");
        pageElePath.actionChains(li);
        pageElePath.click(li);
        try {
            firstNameAfterClickEle= pageElePath.selectByTagName(specWrap,"a");
            firstNameAfterClickEleStr = firstNameAfterClickEle.getText();
        }catch (Exception e){
            log.info("" +e.toString());
            log.info("firstNameAfterClickEle is null");
            firstNameAfterClickEle = null;
            firstNameAfterClickEleStr = null;
        }

        //由在售进入停售 成功
        if (firstNameEle == null && firstNameAfterClickEle != null){
            return true;
        }

        //停售间切换 成功
        if (firstNameEle != null
                && firstNameAfterClickEle != null
                && !firstNameEleStr.equals(firstNameAfterClickEleStr)){
            return true;
        }

        //该年款没有数据,继续下一个年款 成功
        specWrap = pageElePath.selectById(driver,"specWrap-3");
        if (!pageElePath.waitEle(specWrap,By.className("halt-spec"),5L) && pageElePath.waitEle(specWrap,By.className("spec-blank"),5L)){
            log.info("该年款没有数据,继续下一个年款 : ,brand :" + brand + ",series :" + series + ",year :" +year);
            return false;
        }

        //其他情况说明点击tab失败，重复操作
        deep++;
        log.info("重复操作 deep：" +deep);
        return switchTab(li,deep);
    }


    /**
     * 获取第三级数据
     */
    @Override
    @Transactional
    public void getLevel3(WebDriver driver1,CarCategory carCategory) {
        this.driver = driver1;
        parentId = carCategory.getId();
        level = 3;
        firstLetter = carCategory.getFirstLetter();
        brand = carCategory.getBrand();
        series = carCategory.getSeries();

        autoHomeDao.modifyStatus(parentId,1);

        log.info("开始爬虫："+ carCategory.getUrl());
        driver.get(carCategory.getUrl());

        if (!pageElePath.waitEle(driver, By.className("series-list"),5L)){
            log.info("没有数据");
            autoHomeDao.modifyStatus(parentId,3);
            return;
        }

        tempList.clear();

        //即将售卖车型
        if (pageElePath.waitEle(driver,By.cssSelector("[data-target=\"#specWrap-1\"]"),5L)){
            WebElement specWrapTab2 = pageElePath.selectByCssSelector(driver,"[data-target=\"#specWrap-1\"]");
            pageElePath.click(specWrapTab2);
            getCarCategory("specWrap-1");
        }
        //正在售卖车型
        if (pageElePath.waitEle(driver,By.cssSelector("[data-target=\"#specWrap-2\"]"),5L)){
            WebElement specWrapTab2 = pageElePath.selectByCssSelector(driver,"[data-target=\"#specWrap-2\"]");
            pageElePath.click(specWrapTab2);
            getCarCategory("specWrap-2");
        }


        //爬停售车型

        //若不存在停售款元素，结束该次循环
        if (!pageElePath.waitEle(driver,By.className("more-dropdown"),5L)){
            log.info("不存在停售款元素");
            updateData();
            return;
        }

        //停售目录为空，结束该次循环
        List<WebElement> liList = pageElePath.selectByCssSelectors(driver,"#haltList > li");
        if (liList == null){
            log.info("停售目录为空");
            updateData();
            return;
        }

        //爬停售车型
        forTab:for (WebElement li :liList){
            WebElement specWrap = pageElePath.selectById(driver,"specWrap-3");
            year = li.getText();
            while (year.isEmpty()){
                pageElePath.actionChains(li);
                year = li.getText();
            }


            //点击前的元素
            try {
                firstNameEle = pageElePath.selectByTagName(specWrap,"a");
                if (firstNameEle == null){
                    firstNameEleStr = null;
                }else {
                    log.info("firstNameEle is null");
                    firstNameEleStr = firstNameEle.getText();
                }
            }catch (Exception e){
                log.info("firstNameEle is null, error");
                firstNameEle = null;
                firstNameEleStr = null;
            }


            //点击，记录点击后的元素，并比较
            if (switchTab(li,0)){
                //爬停售年系数据
                getCarCategory("specWrap-3");
            }
        }
        log.info("已全部爬取");
        updateData();
    }


    @Override
    @Transactional
    public void getLevel3V2(WebDriver driver1, CarCategory carCategory) {
        this.driver = driver1;
        parentId = carCategory.getId();
        level = 3;
        firstLetter = carCategory.getFirstLetter();
        brand = carCategory.getBrand();
        series = carCategory.getSeries();

        log.info("开始爬虫："+ carCategory.getUrl());
        driver.get(carCategory.getUrl());

        if (!pageElePath.waitEle(driver, By.cssSelector("[data-trigger=\"click\"]"),5L)){
            log.info("没有数据");
            autoHomeDao.modifyStatus(parentId,4);
            return;
        }

        tempList.clear();

        WebElement ulEle = pageElePath.selectByCssSelector(driver,"[data-trigger=\"click\"]");
        List<WebElement> liList = pageElePath.selectListByTagName(ulEle,"li");
        for (WebElement ele :liList){


            if ("更多".equals(ele.getText())){
                getDropMore(ele);
                break;
            }
            year = ele.getText();
            pageElePath.click(ele);
            String cssName = ele.findElement(By.tagName("a")).getAttribute("data-target")+"> div.models > div.modelswrap";
            WebElement modelsWrapEle = pageElePath.selectByCssSelectors(driver,cssName,1);
            List<WebElement> nameEleList = pageElePath.selectByCssSelectors(modelsWrapEle,"a[title]");
            for (WebElement nameEle:nameEleList){
                getNameAndSpecId(nameEle);
                CarCategory carCategory3 = new CarCategory();
                carCategory3.setVersion(version);
                carCategory3.setLevel(level);
                carCategory3.setParentId(parentId);
                carCategory3.setFirstLetter(firstLetter);
                carCategory3.setBrand(brand);
                carCategory3.setSeries(series);
                carCategory3.setYear(year);
                carCategory3.setName(name);
                carCategory3.setCarType("C");
                carCategory3.setSpecId(specId);
                tempList.add(carCategory3);
                log.info(carCategory3.toString());
            }
        }
        updateData();
    }

    private void getDropMore(WebElement liEle){
        WebElement dropMore = pageElePath.selectById(driver,"dropMore");
        for (WebElement tabEle : pageElePath.selectListByTagName(dropMore,"a")){
            pageElePath.actionChains(liEle);
            year = tabEle.getText();
            pageElePath.click(tabEle);
            String cssName = tabEle.getAttribute("data-target")+"> div.models > div.modelswrap";
            WebElement modelsWrapEle = pageElePath.selectByCssSelectors(driver,cssName,1);
            List<WebElement> nameEleList = pageElePath.selectByCssSelectors(modelsWrapEle,"a[title]");
            for (WebElement nameEle:nameEleList){
                getNameAndSpecId(nameEle);
                CarCategory carCategory3 = new CarCategory();
                carCategory3.setVersion(version);
                carCategory3.setLevel(level);
                carCategory3.setParentId(parentId);
                carCategory3.setFirstLetter(firstLetter);
                carCategory3.setBrand(brand);
                carCategory3.setSeries(series);
                carCategory3.setYear(year);
                carCategory3.setName(name);
                carCategory3.setCarType("C");
                carCategory3.setSpecId(specId);
                tempList.add(carCategory3);
                log.info(carCategory3.toString());
            }
        }
    }

    private void getNameAndSpecId(WebElement nameEle){
        try{
            name = nameEle.getText();
        }catch (Exception e){
            log.error(""+e.toString());
            log.error("set name = 名字未找到");
            name = "名字未找到";
        }
        try {
            //获取url https://www.autohome.com.cn/spec/45512/#pvareaid=3454492
            String urlStr = nameEle.getAttribute("href");
            URL url = new URL(urlStr);
            //获取fileStr 如 /spec/45512/
            String fileStr = url.getFile();
            //获取specIdStr 45512
            String specIdStr = fileStr.substring(fileStr.indexOf("/",1)+1,fileStr.length()-1);
            specId = Integer.valueOf(specIdStr);
        }catch (Exception e){
            log.error(""+e.toString());
            log.error("set specId = -1");
            specId = -1;
        }
    }

}
