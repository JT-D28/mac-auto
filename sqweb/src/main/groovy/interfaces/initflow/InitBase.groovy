package interfaces.initflow

import entity.customerandcar.ShopCustomerAndCar
import entity.initInfo.Initdata
import entity.shop.ShopItem
import entity.shop.ShopParts
import org.junit.Test
import org.testingisdocumenting.webtau.browser.driver.CurrentWebDriver

import java.text.SimpleDateFormat

import static org.testingisdocumenting.webtau.WebTauCore.sleep
import static org.testingisdocumenting.webtau.WebTauDsl.browser
import static org.testingisdocumenting.webtau.WebTauDsl.http

class InitBase {

    static valueConfig = new ConfigSlurper().parse(new File("src/test/resources/baseUrl.properties").toURI().toURL())
    static String nowDate=new SimpleDateFormat("yyyyMMddHHmmss").format(new Date())
    static Initdata initData = new CreateInitDataInfo().createInitDataInfo()

    String faunaBase=valueConfig.faunaUrl
    String launaBase=valueConfig.launaUrl

    //系统管理员变量
    String admin_fauna_cookie
    String admin_launa_cookie
    def admin_user_id
    String admin_mobile=valueConfig.adminMobile

    //登录用户变量
    String cus_mobile
    String cus_fauna_cookie
    String cus_launa_cookie
    def cus_user_id
    def cus_storeId
    def cus_userBuyerType
    Boolean cus_isShopExist = false

    InitBase(){}
    InitBase(String initMobilePhone){
        cus_mobile = initMobilePhone
        //用户不存在 创建用户
        def deep =0
        while (!isUserExist()){
            if (deep >2){
                throw RuntimeException
            }
            createUser()
//            sleep(5*1000)
            deep ++
        }
        deep =0
        while (!isShopExist()){
            if (deep >2){
                throw RuntimeException
            }
            createShop()
            sleep(30*1000)
            shopDataInit()
        }

    }

    InitBase(String initMobilePhone,String password){
        cus_mobile = initMobilePhone
        cus_userBuyerType = isUserExist(initMobilePhone,password)
    }

    //检查神汽链门店是否存在
    void init(String initMobile){
        cus_mobile = initMobile
        String userBuyerType=isUserExist()
        //若用户不存在，需创建用户
        if ( isUserExist() == null){
            createUser()
            userBuyerType=isUserExist()
        }
        //B用户已存在门店
        if ( "B".equals(userBuyerType) && isShopExist()){
            //判断服务项目和配件是否创建
        }
        //B用户不存在门店
        if ( "B".equals(userBuyerType) && !isShopExist()){
            //创建门店
            createShop()
            println("sleep 10s ")
            sleep(10*1000)
            //门店数据初始化
            shopDataInit()
        }
        //C客户
        if ( "C".equals(userBuyerType)){
            //创建门店
            createShop()
            println("sleep 30s ")
            sleep(30*1000)
            //门店数据初始化
            shopDataInit()
        }
    }

    Boolean isUserExist(){
        return isUserExist(cus_mobile)
    }

    Boolean isUserExist(String loginMobile){
        return isUserExist(loginMobile,"e10adc3949ba59abbe56e057f20f883e")
    }

    Boolean isUserExist(String loginMobile,String password){
        def queryParams = "{\"mobilephone\": \"" + loginMobile + "\", \"md5Password\": \""+password+"\"}"

        return http.post(faunaBase + "/user/login", http.body("application/json", queryParams)) {
            statusCode.should == 200
            if (body.success == true){
                cus_userBuyerType = body.data.buyerType
                cus_fauna_cookie = data.sid
                cus_user_id = data.id
                if (body.data.storeId != null){
                    cus_storeId = body.data.storeId
                }
            }
            return body.success
        }
    }

    Boolean isShopExist(){
        if (cus_isShopExist == false){
            launaLogin(cus_mobile)
        }
        return cus_isShopExist
    }

    void createUser(){
        println("=================创建用户=================")
        http.get(faunaBase + "/user/getVerifyCode") {
            statusCode.should == 200
            success.should == true
            cus_fauna_cookie = header["Set-cookie"].toString()
        }

        def queryParams = "{\"mobilephone\":\"" + cus_mobile +"\",\"md5Password\":\"e10adc3949ba59abbe56e057f20f883e\",\"verifyCode\":\"sqzx\"}"
        http.post(faunaBase + "/user/preRegister", http.header('Cookie', cus_fauna_cookie), http.body("application/json", queryParams)) {
            statusCode.should == 200
            success.should == true
        }

        http.get(faunaBase + "/user/sendMessageVerifyCode?_t=1624865319078&mobilephone="+cus_mobile+"&verifyCode=sqzx", http.header('Cookie', cus_fauna_cookie)) {
            statusCode.should == 200
            success.should == true
        }

        def querParames2="{\"mobilephone\":\""+cus_mobile+"\",\"md5Password\":\"e10adc3949ba59abbe56e057f20f883e\",\"messageVerifyCode\":\"1\",\"verifyCode\":\"sqzx\"}"
        http.post(faunaBase + "/user/register", http.header('Cookie', cus_fauna_cookie), http.body("application/json", querParames2)) {
            statusCode.should == 200
            success.should == true
            cus_user_id = body.data.id
            cus_isShopExist = false
            cus_userBuyerType = "C"
        }

    }
    void createShop(){
        println("=================创建门店=================")
        chargeMoney()
        signContract()
    }

    void chargeMoney(){
        println("=================充钱=================")
        if (cus_fauna_cookie == null){
            faunaLogin(cus_mobile,"fauna_cookie")
        }
        http.get(faunaBase + "/loan/getCreditInfo/auth?_t=1624868758000", http.header('Cookie', cus_fauna_cookie)) {
            statusCode.should == 200
            success.should == true
        }
        http.get(faunaBase + "/deposit/agreeDeposit/auth", http.header('Cookie', cus_fauna_cookie)) {
            statusCode.should == 200
            success.should == true
        }
        def deposit_account_id = http.get(faunaBase + "/deposit/getDepositAccountInfo/auth", http.header('Cookie', cus_fauna_cookie)) {
            statusCode.should == 200
            success.should == true
            return body.data.id
        }

        if (admin_fauna_cookie == null){
            faunaLogin(admin_mobile,"admin_cookie")
        }
        http.get(faunaBase + "/api/misTest2/depositByAccountId?depositAccountId="+deposit_account_id+"&amount=100000", http.header('Cookie', admin_fauna_cookie)) {
            statusCode.should == 200
            success.should == true
        }
    }

    void signContract(){
        println("=================提交合同=================")
        if (cus_fauna_cookie == null || cus_user_id == null || cus_userBuyerType == null){
            faunaLogin(cus_mobile,"fauna_cookie")
        }
        def queryParams
        if (cus_userBuyerType == "C"){
            queryParams = "{\"salesPrice\":1888,\"type\":\"SQL\",\"subType\":\"common\",\"mobile\":\""+cus_mobile+"\",\"contact\":\"自动化测试\",\"buyerStoreName\":\"自动化测试\",\"remark\":\"\",\"serDetail\":[{\"pkgName\":\"神汽链至尊版（1888元）\",\"contractDetail\":[{\"detailType\":\"SUPPORT_STORE_BASE\",\"detailSalesPrice\":100,\"detailOriPrice\":1000,\"funItemName\":\"神汽链基础服务费\",\"funType\":\"tech\",\"funGroupItemId\":1713,\"funItemId\":1076,\"detailOptionCheck\":\"-1\",\"detailUnit\":\"year\",\"feeVersion\":null,\"isShow\":\"Y\"},{\"detailType\":\"SUPPORT_STORE_COUNT\",\"detailSalesPrice\":1408,\"detailOriPrice\":1000,\"funItemName\":\"支持门店店数\",\"funType\":\"tech_extend\",\"funGroupItemId\":1831,\"funItemId\":1075,\"detailOptionCheck\":\"0\",\"detailUnit\":\"year\",\"feeVersion\":\"1\",\"isShow\":\"Y\"},{\"detailType\":\"VIN_SEARCH\",\"detailSalesPrice\":60,\"detailOriPrice\":60,\"funItemName\":\"VIN码查询次数终身\",\"funType\":\"tech_extend\",\"funGroupItemId\":1945,\"funItemId\":1090,\"detailOptionCheck\":\"0\",\"detailUnit\":\"year\",\"feeVersion\":\"1000\",\"isShow\":\"N\"},{\"detailType\":\"DATA_STORAGE_SHOW\",\"detailSalesPrice\":0,\"detailOriPrice\":0,\"funItemName\":\"支持门店时长\",\"funType\":\"tech\",\"funGroupItemId\":1832,\"funItemId\":1096,\"detailOptionCheck\":\"0\",\"detailUnit\":\"year\",\"feeVersion\":null,\"isShow\":\"Y\"},{\"detailType\":\"IMG_STORAGE\",\"detailSalesPrice\":120,\"detailOriPrice\":120,\"funItemName\":\"图片存储张数终身\",\"funType\":\"tech_extend\",\"funGroupItemId\":1946,\"funItemId\":1091,\"detailOptionCheck\":\"0\",\"detailUnit\":\"year\",\"feeVersion\":\"3000\",\"isShow\":\"N\"},{\"detailType\":\"SUPPORT_STORE_ONE_TIME\",\"detailSalesPrice\":100,\"detailOriPrice\":999,\"funItemName\":\"神汽链年费\",\"funType\":\"tech_extend\",\"funGroupItemId\":1833,\"funItemId\":1083,\"detailOptionCheck\":\"0\",\"detailUnit\":\"year\",\"feeVersion\":\"1\",\"isShow\":\"Y\"},{\"detailType\":\"DATA_STORAGE\",\"detailSalesPrice\":100,\"detailOriPrice\":100,\"funItemName\":\"数据存储条数终身\",\"funType\":\"tech_extend\",\"funGroupItemId\":1947,\"funItemId\":1092,\"detailOptionCheck\":\"0\",\"detailUnit\":\"year\",\"feeVersion\":\"10000\",\"isShow\":\"N\"}],\"salePkgFunGroupId\":1726,\"uniqueKey\":\"dd28c8427019971a9d5f1c48ec6ccb9d\",\"oriPrice\":\"3279\",\"salePrice\":\"1888\"}],\"mouldName\":\"新建神汽链系统订单合同（新）\",\"mouldId\":1052,\"storeApply\":{\"userId\":"+cus_user_id+",\"registerMobile\":\""+cus_mobile+"\",\"contactName\":\"机器人1号\",\"companyName\":\"自动化测试\",\"provinceId\":220000,\"cityId\":220800,\"districtId\":220822,\"streetId\":220822106,\"address\":\"qqqqq\"}}"
        }else if (cus_userBuyerType == "B" && cus_storeId >1000){
            queryParams = "{\"salesPrice\":1888,\"type\":\"SQL\",\"subType\":\"common\",\"mobile\":\""+cus_mobile+"\",\"contact\":\"自动化测试\",\"buyerStoreName\":\"自动化测试\",\"remark\":\"\",\"serDetail\":[{\"pkgName\":\"神汽链至尊版（1888元）\",\"contractDetail\":[{\"detailType\":\"SUPPORT_STORE_BASE\",\"detailSalesPrice\":100,\"detailOriPrice\":1000,\"funItemName\":\"神汽链基础服务费\",\"funType\":\"tech\",\"funGroupItemId\":1713,\"funItemId\":1076,\"detailOptionCheck\":\"-1\",\"detailUnit\":\"year\",\"feeVersion\":null,\"isShow\":\"Y\"},{\"detailType\":\"SUPPORT_STORE_COUNT\",\"detailSalesPrice\":1408,\"detailOriPrice\":1000,\"funItemName\":\"支持门店店数\",\"funType\":\"tech_extend\",\"funGroupItemId\":1831,\"funItemId\":1075,\"detailOptionCheck\":\"0\",\"detailUnit\":\"year\",\"feeVersion\":\"1\",\"isShow\":\"Y\"},{\"detailType\":\"VIN_SEARCH\",\"detailSalesPrice\":60,\"detailOriPrice\":60,\"funItemName\":\"VIN码查询次数终身\",\"funType\":\"tech_extend\",\"funGroupItemId\":1945,\"funItemId\":1090,\"detailOptionCheck\":\"0\",\"detailUnit\":\"year\",\"feeVersion\":\"1000\",\"isShow\":\"N\"},{\"detailType\":\"DATA_STORAGE_SHOW\",\"detailSalesPrice\":0,\"detailOriPrice\":0,\"funItemName\":\"支持门店时长\",\"funType\":\"tech\",\"funGroupItemId\":1832,\"funItemId\":1096,\"detailOptionCheck\":\"0\",\"detailUnit\":\"year\",\"feeVersion\":null,\"isShow\":\"Y\"},{\"detailType\":\"IMG_STORAGE\",\"detailSalesPrice\":120,\"detailOriPrice\":120,\"funItemName\":\"图片存储张数终身\",\"funType\":\"tech_extend\",\"funGroupItemId\":1946,\"funItemId\":1091,\"detailOptionCheck\":\"0\",\"detailUnit\":\"year\",\"feeVersion\":\"3000\",\"isShow\":\"N\"},{\"detailType\":\"SUPPORT_STORE_ONE_TIME\",\"detailSalesPrice\":100,\"detailOriPrice\":999,\"funItemName\":\"神汽链年费\",\"funType\":\"tech_extend\",\"funGroupItemId\":1833,\"funItemId\":1083,\"detailOptionCheck\":\"0\",\"detailUnit\":\"year\",\"feeVersion\":\"1\",\"isShow\":\"Y\"},{\"detailType\":\"DATA_STORAGE\",\"detailSalesPrice\":100,\"detailOriPrice\":100,\"funItemName\":\"数据存储条数终身\",\"funType\":\"tech_extend\",\"funGroupItemId\":1947,\"funItemId\":1092,\"detailOptionCheck\":\"0\",\"detailUnit\":\"year\",\"feeVersion\":\"10000\",\"isShow\":\"N\"}],\"salePkgFunGroupId\":1726,\"uniqueKey\":\"dd28c8427019971a9d5f1c48ec6ccb9d\",\"oriPrice\":\"3279\",\"salePrice\":\"1888\"}],\"mouldName\":\"新建神汽链系统订单合同（新）\",\"mouldId\":1052,\"storeId\":"+cus_mobile+"}"
        }else {
            throw RuntimeException
        }

        def contract_id = http.post(faunaBase + "/apply/contractSubmit/auth", http.header('Cookie', cus_fauna_cookie), http.body("application/json", queryParams)) {
            statusCode.should == 200
            success.should == true
            return body.data.id
        }

        def queryParams2 = "{\"payType\":\"depositPay\",\"amount\":1888,\"contractId\":"+contract_id+",\"depositConsume\":\"sellerContract\"}"
        http.post(faunaBase + "/deposit/paySellerContract/auth", http.header('Cookie', cus_fauna_cookie), http.body("application/json", queryParams2)) {
            statusCode.should == 200
            success.should == true
        }

    }
    void faunaLogin(String mobile, String cookieName){
        String password = "e10adc3949ba59abbe56e057f20f883e"
        faunaLogin(mobile,password,cookieName)
    }
    void faunaLogin(String mobile, String password, String cookieName){
        def queryParams = "{\"mobilephone\": \"" + mobile + "\", \"md5Password\": \""+password+"\"}"
        def data = http.post(faunaBase + "/user/login", http.body("application/json", queryParams)) {
            statusCode.should == 200
            body.success.should == true
            return body.data
        }

        if (cookieName == "fauna_cookie"){
            cus_fauna_cookie = data.sid
            cus_user_id = data.id
        }
        if (cookieName == "admin_cookie"){
            admin_fauna_cookie = data.sid
            admin_user_id = data.id
        }
    }

    void launaLogin(String mobile){
        launaLogin(mobile,"cus")
    }
    void launaLogin(String mobile,String userType) {
        if (userType == null){
            throw RuntimeException
        }
        if (userType == "cus"){
            if (cus_fauna_cookie == null){
                faunaLogin(cus_mobile,"fauna_cookie")
            }
            def token = http.get(faunaBase + "/openid/grant", http.header('Cookie', cus_fauna_cookie)) {
                statusCode.should == 200
                success.should == true
                return body.data.token
            }

            http.get(launaBase + "/openid/acquire?mobile="+mobile+"&token=" + token){
                statusCode.should == 200
                success.should == true
                cus_launa_cookie = header["Set-cookie"].toString()
                if (body.data.canLogin == "Y"){
                    cus_isShopExist = true
                }else {
                    cus_isShopExist = false
                }
            }
        }
        if (userType == "admin"){
            if (admin_fauna_cookie == null){
                faunaLogin(cus_mobile,"admin_cookie")
            }
            def token = http.get(faunaBase + "/openid/grant", http.header('Cookie', admin_fauna_cookie)) {
                statusCode.should == 200
                success.should == true
                return body.data.token
            }

            http.get(launaBase + "/openid/acquire?mobile="+mobile+"&token=" + token){
                statusCode.should == 200
                success.should == true
                admin_launa_cookie = header["Set-cookie"].toString()
            }
        }


    }
    void shopDataInit(){
        //需重新登录，不然会报门店未开通
        launaLogin(cus_mobile)

        for (ShopCustomerAndCar shopCustomerAndCar:initData.getShopCustomerAndCarList()){
            String carNo = shopCustomerAndCar.getCar().getCarNo()
            String customerMobile = shopCustomerAndCar.getCustomer().getMobile()
            String customerName = shopCustomerAndCar.getCustomer().getName()+nowDate
            def queryParams = "{\"saveCarParam\":{\"vinCode\":\"\",\"mileage\":\"\",\"modelId\":\"\",\"engineModel\":\"\",\"engineNumber\":\"\",\"color\":\"\",\"displacement\":\"\",\"lastMaintainTime\":\"\",\"lastMaintainNum\":\"\",\"nextMaintainTime\":\"\",\"nextMaintainNum\":\"\",\"inspectionEndTime\":\"\",\"insureEndTime\":\"\",\"insureCompany\":\"\",\"trafficInsureEndTime\":\"\",\"registerTime\":\"\",\"remark\":\"\",\"seatNum\":\"\",\"carNo\":\""+carNo+"\",\"imgList\":[]},\"saveCustomerParam\":{\"name\":\""+customerName+"\",\"mobile\":\""+customerMobile+"\",\"cusType\":\"odd\",\"address\":\"\",\"birthday\":\"\",\"otherContact\":\"\",\"remark\":\"\",\"provinceId\":\"\",\"cityId\":\"\",\"districtId\":\"\",\"streetId\":\"\",\"gender\":\"S\",\"imgList\":[]}}"
            http.post(launaBase + "/customerAndCar/saveCarAndCustomer", http.header('Cookie', cus_launa_cookie), http.body("application/json", queryParams)) {
                statusCode.should == 200
                success.should == true
            }
        }
        for (ShopItem shopItem:initData.getShopItemList()){
            String itemName = shopItem.getItemName()+nowDate
            def queryParams = "{\"itemName\":\""+itemName+"\",\"catId\":1011,\"itemPrice\":\"100\",\"itemManHour\":\"1\",\"hot\":\"N\",\"shortcut\":\"N\",\"sipList\":[]}"
            http.post(launaBase + "/shopItem/createShopItem", http.header('Cookie', cus_launa_cookie), http.body("application/json", queryParams)) {
                statusCode.should == 200
                success.should == true
            }
        }
        for (ShopParts shopParts:initData.getPartsList()){
            String partsName = shopParts.getPartsName()+nowDate
            def queryParams = "{\"partsName\":\""+partsName+"\",\"partsPrice\":\"20\",\"partsCostPrice\":\"10\",\"unit\":\"\",\"floraPrdLine\":\"other\",\"imgList\":[],\"templateId\":\"\"}"
            http.post(launaBase + "/shopParts/createShopParts", http.header('Cookie', cus_launa_cookie), http.body("application/json", queryParams)) {
                statusCode.should == 200
                success.should == true
            }
        }
    }

    CurrentWebDriver loginLauna(String loginMobile, String passWord) {
        def queryParams = "{\"mobilephone\": \""+loginMobile+"\", \"md5Password\": \""+passWord+"\"}"

        def cookie = http.post(faunaBase + "/user/login", http.body("application/json", queryParams)) {
            statusCode.should == 200
            success.should == true
            return header["Set-cookie"].toString()
        }
        def token = http.get(faunaBase + "/openid/grant", http.header('Cookie', cookie)) {
            statusCode.should == 200
            success.should == true
            return body.data.token
        }
        browser.open(launaBase + "/openid/acquire?token=" + token)
        browser.open(launaBase + "/web")

//        $("[testid=\"弹窗\"] button").click()

        return browser.driver
    }

    @Test
    void demo(){

        cus_mobile="13588210012"
        if(isUserExist() == null){
            println("============创建用户============")
            createUser()
        }
        println("============充钱============")
        chargeMoney()
        signContract("C")
    }

    @Test
    void test(){
        new InitBase("13588210031")
    }
}
