package entity;

import lombok.Data;

/**
 * @author yuxiangfeng
 */
@Data
public class Flow {
    private String bean;
    private String className;
    private String methodName;
    private Object value;
}
