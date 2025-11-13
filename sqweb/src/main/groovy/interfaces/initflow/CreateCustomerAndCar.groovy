package interfaces.initflow

import org.junit.Test
import interfaces.LoginBase
import static org.testingisdocumenting.webtau.WebTauDsl.http


class CreateCustomerAndCar extends LoginBase{

    void createCustomerAndCar(String carNo,String customerMobile,String customerName,String cookie){

        def queryParams = "{\"saveCarParam\":{\"vinCode\":\"\",\"mileage\":\"\",\"modelId\":\"\",\"engineModel\":\"\",\"engineNumber\":\"\",\"color\":\"\",\"displacement\":\"\",\"lastMaintainTime\":\"\",\"lastMaintainNum\":\"\",\"nextMaintainTime\":\"\",\"nextMaintainNum\":\"\",\"inspectionEndTime\":\"\",\"insureEndTime\":\"\",\"insureCompany\":\"\",\"trafficInsureEndTime\":\"\",\"registerTime\":\"\",\"remark\":\"\",\"seatNum\":\"\",\"carNo\":\""+carNo+"\",\"imgList\":[]},\"saveCustomerParam\":{\"name\":\""+customerName+"\",\"mobile\":\""+customerMobile+"\",\"cusType\":\"odd\",\"address\":\"\",\"birthday\":\"\",\"otherContact\":\"\",\"remark\":\"\",\"provinceId\":\"\",\"cityId\":\"\",\"districtId\":\"\",\"streetId\":\"\",\"gender\":\"S\",\"imgList\":[]}}"
        http.post(launaBase + "/customerAndCar/saveCarAndCustomer", http.header('Cookie', cookie), http.body("application/json", queryParams)) {
            statusCode.should == 200
            success.should == true
        }

    }

    void createCustomerAndCar(String carNo,String customerMobile,String customerName){
        def cookie = launaLogin()
        createCustomerAndCar(carNo,customerMobile,customerName,cookie)
    }

    @Test
    void demo(){
        def carNo = "浙A888890"
        def mobile = "18888888890"
        def customerName = "机器人3号"
        createCustomerAndCar(carNo,mobile,customerName)
    }

}
