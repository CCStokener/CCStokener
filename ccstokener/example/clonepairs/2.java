
class Java_2{
public void testUndefined() {
    try {
        buildRule.executeTarget("testUndefined");
        fail("Build exception expected: left out the name attribute");
    } catch (BuildException ex) {
        AntAssert.assertContains("No type specified", ex.getMessage());
    }
}

public void testEchoToBadFile() {
    try {
        buildRule.executeTarget("testEchoToBadFile");
        fail(
            "BuildException should have been thrown on destination file being a directory");
    } catch (BuildException ex) {
        assertContains("destfile is a directory",
                       "destfile is a directory!", ex.getMessage());
    }
}

}
    
