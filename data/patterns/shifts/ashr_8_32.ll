define i32 @pattern_ashr_8_32(i32 %x) {
entry:
  %result = ashr i32 %x, 8
  ret i32 %result
}
