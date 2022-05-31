
class Java_1{
public void testNestedAB() {
    try {
        buildRule.executeTarget("nested.ab");
        fail("Build exception expected: Should have got ambiguous");
    } catch (BuildException ex) {
        AntAssert.assertContains("ambiguous", ex.getMessage());
    }
}

public void testJarAndClassName() {
    try {
        buildRule.executeTarget("testJarAndClassName");
        fail(
            "Build exception should have been thrown - both classname and JAR are not allowed");
    } catch (BuildException ex) {
        assertEquals(
            "Cannot use 'jar' and 'classname' attributes in same command",
            ex.getMessage());
    }
}

}
    
