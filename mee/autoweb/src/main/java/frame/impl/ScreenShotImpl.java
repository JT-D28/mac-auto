package frame.impl;

import frame.ScreenShot;
import org.apache.commons.io.FileUtils;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import java.io.File;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;


/**
 * @author fengyuxiang
 */
@Component
public class ScreenShotImpl implements ScreenShot {

    public static final String TIME = new SimpleDateFormat("yyyyMMddHHmmss").format(new Date());
    @Value("${screenshot.path}")
    String picPath;
    @Value("${screenshot.switch}")
    Boolean screenshotSwitch;


    int picStep = 0;

    @Override
    public void screenShot(WebDriver driver){
        if(!screenshotSwitch){
            return;
        }
        File scrFile = ((TakesScreenshot) driver).getScreenshotAs(OutputType.FILE);
        try {
            String savePath = picPath + "/"+TIME+"/step"+picStep + ".jpg";
            //复制内容到指定文件中
            FileUtils.copyFile(scrFile, new File(savePath));
        } catch (IOException e) {
            e.printStackTrace();
        }
        picStep++;
    }
}
