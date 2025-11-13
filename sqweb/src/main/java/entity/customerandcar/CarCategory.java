package entity.customerandcar;

import com.yuanpin.shared.entity.base.BaseEntity;
import lombok.Data;

/**
 * @author yuxiangfeng
 */
@Data
public class CarCategory extends BaseEntity {

    private String version;

    private Integer level;
    private Long parentId;
    private String firstLetter;
    private String brand;
    private String series;
    private String year;
    private String name;
    private String logo;
    private Long carManufacturerId;
    private String fullIdPath;
    private Long carMaintainManualId;
    private String carType;

    private String url;

    /**
     * 发动机
     */
    private String engine;

    /**
     * 前置四驱
     */
    private String precursor;

    /**
     * 离合档位
     */
    private String gear;

    private int specId;

    private int status;

}
