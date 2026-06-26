import com.android.apksig.ApkSigner;
import java.io.File;
import java.io.FileInputStream;
import java.security.KeyStore;
import java.security.PrivateKey;
import java.security.cert.Certificate;
import java.security.cert.X509Certificate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class SignApk {
    public static void main(String[] args) throws Exception {
        if (args.length != 6) {
            throw new IllegalArgumentException(
                "Usage: SignApk <input.apk> <output.apk> <keystore> <storepass> <alias> <keypass>"
            );
        }

        File input = new File(args[0]);
        File output = new File(args[1]);
        File keystoreFile = new File(args[2]);
        char[] storePassword = args[3].toCharArray();
        String alias = args[4];
        char[] keyPassword = args[5].toCharArray();

        KeyStore keyStore = KeyStore.getInstance("PKCS12");
        try (FileInputStream in = new FileInputStream(keystoreFile)) {
            keyStore.load(in, storePassword);
        }

        PrivateKey privateKey = (PrivateKey) keyStore.getKey(alias, keyPassword);
        if (privateKey == null) {
            throw new IllegalArgumentException("No private key found for alias: " + alias);
        }

        Certificate[] chain = keyStore.getCertificateChain(alias);
        if (chain == null || chain.length == 0) {
            throw new IllegalArgumentException("No certificate chain found for alias: " + alias);
        }

        List<X509Certificate> certificates = new ArrayList<>();
        for (Certificate certificate : chain) {
            certificates.add((X509Certificate) certificate);
        }

        ApkSigner.SignerConfig signerConfig = new ApkSigner.SignerConfig.Builder(
            alias,
            privateKey,
            certificates
        ).build();

        new ApkSigner.Builder(Collections.singletonList(signerConfig))
            .setInputApk(input)
            .setOutputApk(output)
            .setV1SigningEnabled(true)
            .setV2SigningEnabled(true)
            .setV3SigningEnabled(true)
            .setV4SigningEnabled(false)
            .build()
            .sign();
    }
}
