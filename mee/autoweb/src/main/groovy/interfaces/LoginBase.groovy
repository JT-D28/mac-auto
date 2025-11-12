package interfaces

import org.junit.Test

import static org.testingisdocumenting.webtau.WebTauDsl.http

class LoginBase {
    static valueConfig = new ConfigSlurper().parse(new File("src/test/resources/baseUrl.properties").toURI().toURL())
    def faunaBase
    def launaBase
    def loginMobile
    def password

    LoginBase(){
        this.faunaBase=valueConfig.faunaUrl
        this.launaBase=valueConfig.launaUrl
        this.loginMobile=valueConfig.loginMobile
    }
    String faunaLogin(){
        def queryParams = "{\"mobilephone\": \"" + loginMobile + "\", \"md5Password\": \""+password+"\"}"

        return http.post(faunaBase + "/user/login", http.body("application/json", queryParams)) {
            statusCode.should == 200
            success.should == true
            return header["Set-cookie"].toString()
        }
    }

    String launaLogin(){
        def token = getToken()
        return http.get(launaBase + "/openid/acquire?_t=1624932526296&mobile="+loginMobile+"&token=" + token){
            statusCode.should == 200
            success.should == true
            return header["Set-cookie"].toString()
        }
    }

    String getToken(String mobile,String password){
        this.loginMobile=mobile
        this.password=password
        def cookie =faunaLogin()
        return http.get(faunaBase + "/openid/grant", http.header('Cookie', cookie)) {
            statusCode.should == 200
            success.should == true
            return body.data.token
        }
    }

    @Test
    void demo(){
        launaLogin()
    }


}
