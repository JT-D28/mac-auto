package ui.annotaion;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * @author yuxiangfeng
 */
@Target({ElementType.FIELD})
@Retention(RetentionPolicy.RUNTIME)
public @interface UIElement {
    String id() default "";
    String cssSelect() default "";
    String xpath() default "";
    String tag() default "";
    String testId() default "";
    //parent和popup仅一个生效，popup优先
    String parent() default "";
    boolean popup() default false;
    int idx() default 0;
}
