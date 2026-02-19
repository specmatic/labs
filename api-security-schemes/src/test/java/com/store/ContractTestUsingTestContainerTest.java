package com.store;

import com.store.model.DB;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIf;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.BindMode;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.containers.wait.strategy.Wait;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;

import static org.assertj.core.api.Assertions.assertThat;

@Testcontainers
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.DEFINED_PORT)
@ActiveProfiles("prod")
@EnabledIf(value = "isNonCIOrLinux", disabledReason = "Run only on Linux in CI; all platforms allowed locally")
public class ContractTestUsingTestContainerTest {
    public static boolean isNonCIOrLinux() {
        return !"true".equals(System.getenv("CI")) || System.getProperty("os.name").toLowerCase().contains("linux");
    }

    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    private static final GenericContainer<?> keycloakContainer = new GenericContainer<>("quay.io/keycloak/keycloak:22.0.5")
            .withCommand("start-dev --import-realm")
            .withFileSystemBind("./keycloak", "/opt/keycloak/data/import", BindMode.READ_ONLY)
            .withEnv("KEYCLOAK_IMPORT", "/opt/keycloak/data/import/specmatic-realm.json")
            .withEnv("KEYCLOAK_ADMIN", "admin")
            .withEnv("KEYCLOAK_ADMIN_PASSWORD", "admin")
            .withExposedPorts(8080)
            .waitingFor(Wait.forHttp("/realms/specmatic/.well-known/openid-configuration").forStatusCode(200))
            .withLogConsumer(outputFrame -> System.out.print(outputFrame.getUtf8String()));

    private static final GenericContainer<?> testContainer = new GenericContainer<>("specmatic/specmatic:latest")
            .withCommand("test")
            .withEnv("APP_BASE_URL", "http://host.docker.internal:8080")
            .withFileSystemBind("./spec", "/usr/src/app/spec", BindMode.READ_ONLY)
            .withFileSystemBind("./specmatic.yaml", "/usr/src/app/specmatic.yaml", BindMode.READ_ONLY)
            .withFileSystemBind("./build/reports/specmatic", "/usr/src/app/build/reports/specmatic", BindMode.READ_WRITE)
            .waitingFor(Wait.forLogMessage(".*Tests run:.*", 1))
            .withExtraHost("host.docker.internal", "host-gateway")
            .withLogConsumer(outputFrame -> System.out.print(outputFrame.getUtf8String()));

    @DynamicPropertySource
    static void setProperties(DynamicPropertyRegistry registry) {
        startKeycloakIfRequired();
        registry.add("spring.security.oauth2.resourceserver.jwt.issuer-uri", ContractTestUsingTestContainerTest::issuerUri);
    }

    @BeforeAll
    public static void setup() throws Exception {
        DB.INSTANCE.resetDB();
        startKeycloakIfRequired();
        String oauthToken = fetchOAuthToken();
        testContainer.withEnv("OAUTH_TOKEN", oauthToken);
    }

    @Test
    public void specmaticContractTest() {
        testContainer.start();
        boolean hasSucceeded = testContainer.getLogs().contains("Failures: 0");
        assertThat(hasSucceeded).isTrue();
    }

    private static void startKeycloakIfRequired() {
        if (!keycloakContainer.isRunning()) {
            keycloakContainer.start();
        }
    }

    private static String issuerUri() {
        return keycloakBaseUrl() + "/realms/specmatic";
    }

    private static String keycloakBaseUrl() {
        return "http://" + keycloakContainer.getHost() + ":" + keycloakContainer.getMappedPort(8080);
    }

    private static String fetchOAuthToken() throws Exception {
        String form = "grant_type=password"
                + "&client_id=" + encode("order-api")
                + "&username=" + encode("user1")
                + "&password=" + encode("password")
                + "&scope=" + encode("profile email");

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(keycloakBaseUrl() + "/realms/specmatic/protocol/openid-connect/token"))
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(form))
                .build();

        HttpResponse<String> response = HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) {
            throw new IllegalStateException("Failed to fetch OAuth token from Keycloak. HTTP " + response.statusCode() + " body: " + response.body());
        }

        JsonNode jsonNode = OBJECT_MAPPER.readTree(response.body());
        String accessToken = jsonNode.path("access_token").asText("");
        if (accessToken.isBlank()) {
            throw new IllegalStateException("Keycloak did not return access_token. Response: " + response.body());
        }
        return accessToken;
    }

    private static String encode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }
}
