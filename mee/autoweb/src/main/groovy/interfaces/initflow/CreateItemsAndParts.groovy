package interfaces.initflow

import interfaces.LoginBase
import org.junit.Test

import static org.testingisdocumenting.webtau.WebTauDsl.http

class CreateItemsAndParts extends LoginBase{
    void createItem(String itemName){
        def cookie = launaLogin()
        def queryParams = "{\"itemName\":\""+itemName+"\",\"catId\":1011,\"itemPrice\":\"100\",\"itemManHour\":\"1\",\"hot\":\"N\",\"shortcut\":\"N\",\"sipList\":[]}"
        http.post(launaBase + "/shopItem/createShopItem", http.header('Cookie', cookie), http.body("application/json", queryParams)) {
            statusCode.should == 200
            success.should == true
        }
    }

    void createParts(String partsName){
        def cookie = launaLogin()
        def queryParams = "{\"partsName\":\""+partsName+"\",\"partsPrice\":\"20\",\"partsCostPrice\":\"10\",\"unit\":\"\",\"floraPrdLine\":\"other\",\"imgList\":[],\"templateId\":\"\"}"
        http.post(launaBase + "/shopParts/createShopParts", http.header('Cookie', cookie), http.body("application/json", queryParams)) {
            statusCode.should == 200
            success.should == true
        }
    }

    @Test
    void demo(){
//        createItem("洗车2")
        createParts("坐垫2")
    }
}
