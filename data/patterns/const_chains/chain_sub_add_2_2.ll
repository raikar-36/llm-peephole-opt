define i32 @chain_sub_add_2_2(i32 %x) {
entry:
  %tmp = sub i32 %x, 2
  %result = add i32 %tmp, 2
  ret i32 %result
}
