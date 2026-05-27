define i32 @pattern_add_neg128_32(i32 %x) {
entry:
  %result = add i32 %x, -128
  ret i32 %result
}
