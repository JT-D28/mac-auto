package entity.customerandcar;

import com.yuanpin.shared.entity.base.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

import java.util.Date;

@EqualsAndHashCode(callSuper = true)
@Data
public class Car extends BaseEntity {

    private String carNo;
    private String vinCode;
    private Long carBrandId;
    private Long carSeriesId;
    private Long yearId;
    private Long modelId;
    private String color;
    private Long mileage;
    private Date registerTime;
    private String displacement;
    private String engineModel;
    private String engineNumber;
    private Date lastMaintainTime;
    private Date nextMaintainTime;
    private Long lastMaintainNum;
    private Long nextMaintainNum;
    private String insureCompany;
    private Date insureEndTime;
    private Date inspectionEndTime;
    private String remark;
    private String img;
    private String licenseType;
    private String axleNo;
    private String fuelType;

}
