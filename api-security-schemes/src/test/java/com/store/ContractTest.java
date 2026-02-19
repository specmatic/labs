package com.store;

import com.store.model.DB;
import io.specmatic.test.SpecmaticContractTest;
import io.specmatic.test.SpecmaticJUnitSupport;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;

public class ContractTest implements SpecmaticContractTest {
    private static ConfigurableApplicationContext context;

    @BeforeAll
    public static void setUp() {
        DB.INSTANCE.resetDB();

        context = SpringApplication.run(Application.class);
    }

    @AfterAll
    public static void tearDown() {
        context.close();
    }
}
